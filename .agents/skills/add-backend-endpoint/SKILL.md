---
name: add-backend-endpoint
description: Step-by-step workflow for adding a new gRPC/HTTP endpoint to the Go backend service, including proto definitions, SQL queries, handler implementation, gateway registration, and tests.
---

## When to use this skill

Use this skill when adding a new API endpoint to the Go backend service. This covers adding an RPC to an existing domain (user, journal, analytics) or creating an entirely new domain/service.

## Architecture

The backend uses gRPC with grpc-gateway. The flow is:

```
HTTP request → gRPC-Gateway (:8080) → gRPC Server (:50051) → Handler → DB (via sqlc)
```

HTTP routes are defined as annotations in proto files -- there are no separate HTTP routers.

## Step-by-step workflow

### Step 1: Add SQL queries (if new DB access is needed)

Add queries to `services/backend/internal/sql/queries/{domain}.sql`. Use the sqlc annotation format:

```sql
-- name: GetWidgetById :one
SELECT * FROM source.widgets WHERE id = $1;

-- name: ListWidgets :many
SELECT * FROM source.widgets ORDER BY created_at DESC LIMIT $1 OFFSET $2;

-- name: CreateWidget :one
INSERT INTO source.widgets(name, user_id) VALUES ($1, $2) RETURNING *;
```

Annotations: `:one` (single row), `:many` (multiple rows), `:exec` (no return).

If a new table is needed, add a schema migration file in `services/backend/internal/sql/schema/` following the `NNN_description.sql` naming convention.

Run code generation:

```bash
make sqlc-generate
```

This regenerates `services/backend/internal/db/` including `querier.go`, `models.go`, and query implementation files. **Do not edit files in `internal/db/` directly.**

### Step 2: Define proto messages and service RPCs

**For an existing domain** (e.g., journal), edit the existing proto files:

- Message types: `services/backend/proto/{domain}/{domain}.proto`
- Service RPCs: `services/backend/proto/{domain}/{domain}_service.proto`

**For a new domain**, create both files under `services/backend/proto/{new_domain}/`.

Message definition example (`{domain}.proto`):

```protobuf
syntax = "proto3";

package {domain};

option go_package = "github.com/jyablonski/lotus/internal/pb/proto/{domain};{domain}_pb";

message GetWidgetRequest {
  string widget_id = 1;
}

message GetWidgetResponse {
  string widget_id = 1;
  string name = 2;
  string created_at = 3;
}
```

Service definition example (`{domain}_service.proto`):

```protobuf
syntax = "proto3";

package {domain};

option go_package = "github.com/jyablonski/lotus/internal/pb/proto/{domain};{domain}_pb";

import "google/api/annotations.proto";
import "proto/{domain}/{domain}.proto";

service {Domain}Service {
  rpc GetWidget(GetWidgetRequest) returns (GetWidgetResponse) {
    option (google.api.http) = {
      get: "/v1/widgets/{widget_id}"
    };
  }
}
```

Common HTTP method patterns:

- `get: "/v1/resources"` -- list
- `get: "/v1/resources/{id}"` -- get by ID
- `post: "/v1/resources"` with `body: "*"` -- create
- `put: "/v1/resources/{id}"` with `body: "*"` -- update
- `delete: "/v1/resources/{id}"` -- delete

Omit the `google.api.http` option for gRPC-only RPCs (no REST endpoint).

Run code generation:

```bash
make buf-generate
```

This regenerates `services/backend/internal/pb/proto/{domain}/` with `*.pb.go`, `*_grpc.pb.go`, and `*.pb.gw.go` files. **Do not edit files in `internal/pb/` directly.**

### Step 3: Implement the gRPC handler

**For an existing domain**, add the method to the existing server struct in `services/backend/internal/grpc/{domain}_service.go`.

**For a new domain**, create `services/backend/internal/grpc/{new_domain}_service.go`:

```go
package grpc

import (
    "context"
    "fmt"
    "log/slog"

    "github.com/jyablonski/lotus/internal/db"
    pb "github.com/jyablonski/lotus/internal/pb/proto/{domain}"
)

type {Domain}Server struct {
    pb.Unimplemented{Domain}ServiceServer
    DB     db.Querier
    Logger *slog.Logger
}

func {Domain}Service(q db.Querier, logger *slog.Logger) *{Domain}Server {
    return &{Domain}Server{
        DB:     q,
        Logger: logger,
    }
}

func (s *{Domain}Server) GetWidget(ctx context.Context, req *pb.GetWidgetRequest) (*pb.GetWidgetResponse, error) {
    // 1. Parse/validate input
    // 2. Call s.DB.SomeQuery(ctx, params)
    // 3. Map DB model to proto response
    // 4. Return response, or gRPC status error on failure
}
```

Key conventions:

- Use `db.Querier` interface (not `*db.Queries` concrete type) for testability.
- Use `log/slog` for structured logging.
- Return gRPC status errors: `status.Errorf(codes.NotFound, "widget not found")`.
- Log errors with context before returning them.
- If the service makes outbound HTTP calls, add an `HTTPClient` field (see `JournalServer` for reference).

### Step 4: Register the service (new domains only)

Skip this step if adding an RPC to an existing service.

**In `services/backend/internal/grpc/server.go`**, register the new service:

```go
import pb_{domain} "github.com/jyablonski/lotus/internal/pb/proto/{domain}"

// Inside StartGRPCServer():
pb_{domain}.Register{Domain}ServiceServer(grpcServer, {Domain}Service(queries, logger))
```

**In `services/backend/internal/main.go`**, register the gateway handler:

```go
import {domain}_pb "github.com/jyablonski/lotus/internal/pb/proto/{domain}"

// Inside the gRPC-Gateway goroutine:
err = {domain}_pb.Register{Domain}ServiceHandlerFromEndpoint(ctx, mux, "localhost:50051", opts)
if err != nil {
    logger.Error("Failed to register {Domain}Service gRPC-Gateway", "error", err)
}
```

### Step 5: Regenerate mocks

If the `Querier` interface changed (new SQL queries were added):

```bash
make moq-generate
```

This regenerates `services/backend/internal/mocks/querier_mock.go`. **Do not edit files in `internal/mocks/` directly.**

### Step 6: Write tests

Add unit tests in `services/backend/internal/grpc/{domain}_service_test.go`. Use package `grpc_test` (external test package) with `testify` assertions and `moq`-generated mocks.

```go
package grpc_test

import (
    "context"
    "testing"

    "github.com/jyablonski/lotus/internal/db"
    internalgrpc "github.com/jyablonski/lotus/internal/grpc"
    "github.com/jyablonski/lotus/internal/mocks"
    pb "github.com/jyablonski/lotus/internal/pb/proto/{domain}"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func Test{Domain}Server_GetWidget_Success(t *testing.T) {
    mockQuerier := &mocks.QuerierMock{
        GetWidgetByIdFunc: func(ctx context.Context, id int32) (db.Widget, error) {
            return db.Widget{ID: 1, Name: "test"}, nil
        },
    }

    server := internalgrpc.{Domain}Service(mockQuerier, newTestLogger())

    resp, err := server.GetWidget(context.Background(), &pb.GetWidgetRequest{WidgetId: "1"})

    require.NoError(t, err)
    require.NotNil(t, resp)
    assert.Equal(t, "1", resp.WidgetId)
    assert.Len(t, mockQuerier.GetWidgetByIdCalls(), 1)
}
```

Test patterns to cover:

- Success case
- Invalid input (bad UUIDs, missing fields)
- DB errors
- Not found cases
- Pagination defaults and limits (if applicable)

Run tests:

```bash
cd services/backend && go test ./internal/grpc/...
```

## Pre-commit hooks

These run automatically and handle regeneration:

- `sqlc-generate` when SQL files change
- `buf-generate` when proto files change
- `moq-generate` when `internal/db/querier.go` or `internal/grpc/interfaces.go` change
- `go-fmt` on all Go files

## Quick reference: key file paths

| What                             | Path                                                      |
| -------------------------------- | --------------------------------------------------------- |
| Proto definitions                | `services/backend/proto/{domain}/`                        |
| SQL queries                      | `services/backend/internal/sql/queries/{domain}.sql`      |
| SQL schema                       | `services/backend/internal/sql/schema/`                   |
| Handler implementations          | `services/backend/internal/grpc/{domain}_service.go`      |
| Unit tests                       | `services/backend/internal/grpc/{domain}_service_test.go` |
| gRPC server setup                | `services/backend/internal/grpc/server.go`                |
| Main / gateway registration      | `services/backend/internal/main.go`                       |
| Generated DB code (read-only)    | `services/backend/internal/db/`                           |
| Generated proto code (read-only) | `services/backend/internal/pb/`                           |
| Generated mocks (read-only)      | `services/backend/internal/mocks/`                        |
| sqlc config                      | `services/backend/sqlc.yaml`                              |
| buf config                       | `services/backend/buf.yaml`, `buf.gen.yaml`               |
