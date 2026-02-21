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

    "github.com/jyablonski/lotus/internal/inject"
    pb "github.com/jyablonski/lotus/internal/pb/proto/{domain}"
)

type {Domain}Server struct {
    pb.Unimplemented{Domain}ServiceServer
}

func (s *{Domain}Server) GetWidget(ctx context.Context, req *pb.GetWidgetRequest) (*pb.GetWidgetResponse, error) {
    // 1. Parse/validate input (before extracting deps, so validation
    //    tests don't need a fully-populated context)

    // 2. Extract dependencies from context
    dbq := inject.DBFrom(ctx)
    logger := inject.LoggerFrom(ctx)

    // 3. Call dbq.SomeQuery(ctx, params)
    // 4. Map DB model to proto response
    // 5. Return response, or gRPC status error on failure
}
```

Key conventions:

- Service structs are **empty** (only embed `Unimplemented*Server`). There are no `DB`, `Logger`, or other fields -- all dependencies come from context via the `internal/inject` package.
- A gRPC unary interceptor in `main.go` populates every request context with `db.Querier`, `*slog.Logger`, `inject.HTTPDoer`, and the analyzer URL. Service methods extract what they need via `inject.DBFrom(ctx)`, `inject.LoggerFrom(ctx)`, etc.
- **Extract deps after input validation.** This way, tests for validation failures (bad UUIDs, missing fields) can use a bare `context.Background()` without setting up any dependencies.
- Use `log/slog` for structured logging.
- Return gRPC status errors: `status.Errorf(codes.NotFound, "widget not found")`.
- Log errors with context before returning them.
- If the service makes outbound HTTP calls, extract the HTTP client via `inject.HTTPClientFrom(ctx)` (see `JournalServer` for reference). If launching a background goroutine, capture deps into local variables before the `go` call since the request context should not be used after the handler returns.

### Step 4: Register the service (new domains only)

Skip this step if adding an RPC to an existing service.

Both gRPC and gateway registration live in `services/backend/internal/grpc/server.go`. Add the new service to both functions so that `main.go` does not need any changes.

**In `RegisterServices`**, add the gRPC registration:

```go
import pb_{domain} "github.com/jyablonski/lotus/internal/pb/proto/{domain}"

// Inside RegisterServices():
pb_{domain}.Register{Domain}ServiceServer(s, &{Domain}Server{})
```

**In `RegisterGateway`**, add the gateway handler registration:

```go
// Add to the slice inside RegisterGateway():
pb_{domain}.Register{Domain}ServiceHandlerFromEndpoint,
```

No changes to `main.go` are needed -- it calls `RegisterServices` and `RegisterGateway` generically.

### Step 5: Regenerate mocks

If the `Querier` interface changed (new SQL queries were added):

```bash
make moq-generate
```

This regenerates `services/backend/internal/mocks/querier_mock.go`. **Do not edit files in `internal/mocks/` directly.**

### Step 6: Write tests

Add unit tests in `services/backend/internal/grpc/{domain}_service_test.go`. Use package `grpc_test` (external test package) with `testify` assertions and `moq`-generated mocks.

Tests use context-based dependency injection -- create a context with mocked deps using `inject.WithX` helpers, then call the method on an empty server struct:

```go
package grpc_test

import (
    "context"
    "testing"

    "github.com/jyablonski/lotus/internal/db"
    internalgrpc "github.com/jyablonski/lotus/internal/grpc"
    "github.com/jyablonski/lotus/internal/inject"
    "github.com/jyablonski/lotus/internal/mocks"
    pb "github.com/jyablonski/lotus/internal/pb/proto/{domain}"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

// testCtx returns a context populated with a mock Querier.
func testCtx(q db.Querier) context.Context {
    ctx := context.Background()
    ctx = inject.WithDB(ctx, q)
    // Add inject.WithLogger, inject.WithHTTPClient, inject.WithAnalyzerURL
    // as needed by the service methods under test.
    return ctx
}

func Test{Domain}Server_GetWidget_Success(t *testing.T) {
    mockQuerier := &mocks.QuerierMock{
        GetWidgetByIdFunc: func(ctx context.Context, id int32) (db.Widget, error) {
            return db.Widget{ID: 1, Name: "test"}, nil
        },
    }

    server := &internalgrpc.{Domain}Server{}
    ctx := testCtx(mockQuerier)

    resp, err := server.GetWidget(ctx, &pb.GetWidgetRequest{WidgetId: "1"})

    require.NoError(t, err)
    require.NotNil(t, resp)
    assert.Equal(t, "1", resp.WidgetId)
    assert.Len(t, mockQuerier.GetWidgetByIdCalls(), 1)
}

func Test{Domain}Server_GetWidget_InvalidInput(t *testing.T) {
    // Validation-only tests don't need any context deps -- validation
    // runs before inject.DBFrom(ctx), so a bare context is fine.
    server := &internalgrpc.{Domain}Server{}

    _, err := server.GetWidget(context.Background(), &pb.GetWidgetRequest{WidgetId: ""})
    require.Error(t, err)
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

## Sentinel errors

Service files define sentinel errors (`var ErrXxx = errors.New("...")`) for domain-level conditions that callers or tests might check with `errors.Is()`. Sentinels belong at the top of the service file, grouped in a `var` block.

### When to use sentinels

Use a sentinel for **validation and domain conditions** -- things the caller could branch on:

- `ErrInvalidUserID`, `ErrEmailRequired`, `ErrUserNotFound`, `ErrInvalidJournalID`, `ErrJournalNotFound`

Do **not** use sentinels for **operational wrap errors** that just add context to an underlying cause. These stay as plain `fmt.Errorf`:

- `fmt.Errorf("failed to create journal: %w", err)` -- the caller checks the wrapped `err`, not the message prefix

### Shared vs per-service sentinels

- Sentinels used in only one service file are defined in that file.
- Sentinels shared across multiple files in the `grpc` package (e.g., `ErrInvalidUserID` used by both `journal_service.go` and `analytics_service.go`) are defined once in `internal/grpc/errors.go`.

### How to wire sentinels to errors

There are two patterns depending on how the error is returned:

**`fmt.Errorf` wrapping** (non-gRPC returns): wrap with `%w` so `errors.Is()` works:

```go
return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
```

**`status.Error` / `status.Errorf`** (gRPC returns): embed via `.Error()` since gRPC status errors don't support `errors.Is()` on the inner sentinel:

```go
return nil, status.Error(codes.NotFound, ErrUserNotFound.Error())
return nil, status.Errorf(codes.Internal, "%s: %v", ErrGetUserFailed.Error(), err)
```

### Testing sentinels

- For `fmt.Errorf("%w", sentinel)` errors, use `assert.ErrorIs(t, err, internalgrpc.ErrXxx)`.
- For `status.Error(code, sentinel.Error())` errors, `errors.Is()` won't match the sentinel. Use `assert.Contains(t, err.Error(), "...")` or check `status.Code(err)`.

## Quick reference: key file paths

| What                             | Path                                                      |
| -------------------------------- | --------------------------------------------------------- |
| Proto definitions                | `services/backend/proto/{domain}/`                        |
| SQL queries                      | `services/backend/internal/sql/queries/{domain}.sql`      |
| SQL schema                       | `services/backend/internal/sql/schema/`                   |
| Handler implementations          | `services/backend/internal/grpc/{domain}_service.go`      |
| Shared sentinel errors           | `services/backend/internal/grpc/errors.go`                |
| Unit tests                       | `services/backend/internal/grpc/{domain}_service_test.go` |
| gRPC + gateway registration      | `services/backend/internal/grpc/server.go`                |
| Dependency injection helpers     | `services/backend/internal/inject/inject.go`              |
| Main entry point                 | `services/backend/internal/main.go`                       |
| Generated DB code (read-only)    | `services/backend/internal/db/`                           |
| Generated proto code (read-only) | `services/backend/internal/pb/`                           |
| Generated mocks (read-only)      | `services/backend/internal/mocks/`                        |
| sqlc config                      | `services/backend/sqlc.yaml`                              |
| buf config                       | `services/backend/buf.yaml`, `buf.gen.yaml`               |
