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

There are two layers of tests for gRPC services:

#### Unit tests (mocks, no DB)

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

#### Integration tests (real DB)

Add integration tests in `services/backend/internal/grpc/{domain}_service_integration_test.go`. All integration tests use `package grpc_test` (same as unit tests) and share the helpers from `testhelpers_test.go`.

**How the DB container works** (`testmain_test.go`):

`TestMain` starts a single ephemeral postgres container (testcontainers-go) before any test runs and terminates it after all tests finish. The container's connection string is stored in the `testDBConnStr` package-level variable. After `postgres.Run` returns, `TestMain` calls a `waitForDB` retry loop (up to 10s, 500ms intervals) to ensure postgres has truly finished running init scripts before any test connects. This means:

- No external postgres required — `make test-backend` is fully self-contained
- Running tests never touches your local Tilt postgres
- The container starts **once per `go test` invocation**, not once per test function

**Per-test isolation: transaction rollback**
Each `newTestCtx(t)` call opens a fresh `*sql.DB` connection and immediately begins a transaction. `db.New(tx)` is used because sqlc's `New()` accepts the `DBTX` interface, which both `*sql.DB` and `*sql.Tx` satisfy. `t.Cleanup` rolls back the transaction and closes the connection. Since the transaction is never committed, every write is discarded at cleanup — no truncation, no WAL writes.

One implication: if two records are inserted in the same `newTestCtx` transaction within the same millisecond, `ORDER BY created_at DESC` is non-deterministic. Use a map-based assertion or insert records in separate `newTestCtx` calls if ordering matters.

**Shared setup** (`testhelpers_test.go`):

- `newTestCtx(t)` — opens a connection, begins a transaction, registers `t.Cleanup` to roll back and close. Returns `(ctx context.Context, queries *db.Queries)`.
- `withAnalyzer(ctx, url)` — adds HTTP client and analyzer URL to ctx (for journal tests).
- `mockAnalyzerServer(t)` / `failingAnalyzerServer(t)` — httptest servers with `t.Cleanup(srv.Close)` registered automatically.
- `createTestUser(t, queries)` — inserts a minimal OAuth user and returns its UUID.

**Schema** (`testdata/schema.sql`): mirrors `docker/db/01-bootstrap.sql` without seed data or unrelated databases (dagster, mlflow, etc.). Keep these in sync when adding new tables.

Key conventions:

- Call `newTestCtx(t)` at the start of every test that touches the DB. Rollback on cleanup gives a clean slate automatically.
- For tests that only check input validation (bad UUIDs, missing fields), use `context.Background()` directly — no DB setup needed.
- Use `t.Run` for grouping related subtests within a single top-level test function (e.g., pagination variants, or multiple invalid input shapes). Each subtest that needs the DB calls `newTestCtx(t)` independently.
- Log to `io.Discard` (the shared helpers do this automatically) — no `os.Stdout` or `slog.SetDefault` in tests.
- Do not use `time.Sleep` to wait for async goroutines or create timestamp ordering. If ordering matters, insert with explicit timestamps.

```go
package grpc_test

import (
    "context"
    "testing"

    grpcServer "github.com/jyablonski/lotus/internal/grpc"
    pb "github.com/jyablonski/lotus/internal/pb/proto/{domain}"
    "github.com/stretchr/testify/require"
)

func TestIntegration_GetWidget(t *testing.T) {
    t.Run("success", func(t *testing.T) {
        ctx, queries := newTestCtx(t)
        userID := createTestUser(t, queries)
        svc := &grpcServer.{Domain}Server{}

        resp, err := svc.GetWidget(ctx, &pb.GetWidgetRequest{WidgetId: "..."})
        require.NoError(t, err)
        require.NotNil(t, resp)
    })

    t.Run("not_found", func(t *testing.T) {
        ctx, _ := newTestCtx(t)
        svc := &grpcServer.{Domain}Server{}

        _, err := svc.GetWidget(ctx, &pb.GetWidgetRequest{WidgetId: "99999"})
        require.Error(t, err)
    })

    t.Run("invalid_id", func(t *testing.T) {
        // No DB needed — validation fails before any DB access
        svc := &grpcServer.{Domain}Server{}
        _, err := svc.GetWidget(context.Background(), &pb.GetWidgetRequest{WidgetId: "not-a-uuid"})
        require.Error(t, err)
    })
}
```

#### Running tests

```bash
# All tests — testcontainers starts an isolated Postgres automatically, no setup needed
make test-backend

# Or directly
cd services/backend && go test ./internal/grpc/...
```

Test patterns to cover:

- Success case
- Invalid input (bad UUIDs, missing fields) — no DB setup needed, use `context.Background()`
- Not found cases
- Pagination defaults and limits (if applicable)

### Step 7: Update the Bruno API collection

After adding a new endpoint, add a corresponding `.bru` request file to the Bruno collection so the team can test it from the Bruno GUI.

**Backend requests** go in `bruno/backend/`. Create a new `.bru` file named after the endpoint (e.g., `get-widget.bru`):

```bru
meta {
  name: Get Widget
  type: http
  seq: 1
}

get {
  url: {{backend_url}}/v1/widgets/{{widget_id}}
  body: none
  auth: none
}
```

For POST/PUT endpoints with a request body:

```bru
meta {
  name: Create Widget
  type: http
  seq: 2
}

post {
  url: {{backend_url}}/v1/widgets
  body: json
  auth: none
}

body:json {
  {
    "name": "example widget",
    "userId": "{{user_id}}"
  }
}
```

Key conventions:

- Use `{{backend_url}}` for the base URL (resolved from the Bruno environment)
- Use `{{user_id}}`, `{{journal_id}}`, etc. for shared variable references
- Use kebab-case for file names (e.g., `get-user-journal-summary.bru`)
- Disable optional query params with the `~` prefix (e.g., `~model_version:`)
- JSON field names use lowerCamelCase (matching the gRPC-gateway JSON serialization)
- If the endpoint introduces a new variable that other requests might reference, add it to `bruno/environments/local.bru`

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
| Bruno API collection (backend)   | `bruno/backend/`                                          |
| Bruno environment variables      | `bruno/environments/local.bru`                            |
| sqlc config                      | `services/backend/sqlc.yaml`                              |
| buf config                       | `services/backend/buf.yaml`, `buf.gen.yaml`               |
