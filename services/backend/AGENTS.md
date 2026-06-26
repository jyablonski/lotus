# Backend Service - Agent Guide

Go gRPC service with HTTP gateway for core application logic, CRUD operations, and API gateway functionality.

## Technology Stack

- Go
- gRPC with grpc-gateway
- PostgreSQL

## Architecture Patterns

### Service Structure

The backend runs two servers concurrently:

1. gRPC Server (`:50051`) - Core gRPC service
2. gRPC-Gateway (`:8080`) - HTTP gateway that translates HTTP → gRPC

### Code Generation

The service uses code generation for type safety:

- sqlc - Generates Go code from SQL queries
  - SQL files: `internal/sql/queries/`
  - Generated code: `internal/db/`
  - Config: `sqlc.yaml`
  - Run: `make sqlc-generate` or `cd services/backend && sqlc generate`

- buf - Generates gRPC/protobuf code
  - Proto files: `proto/`
  - Generated code: `internal/pb/proto/`
  - Config: `buf.yaml`, `buf.gen.yaml`
  - Run: `make buf-generate` or `cd services/backend && buf generate`

- moq - Generates mock implementations for interfaces
  - Interfaces: `internal/db/querier.go`, `internal/inject/inject.go`
  - Generated mocks: `internal/mocks/`
  - Run: `make moq-generate` or `./scripts/moq-generate.sh`

Important: Always regenerate code after changing SQL queries or proto definitions.

## Code Organization

```
internal/
├── main.go                    # Entry point, starts gRPC and gateway servers
├── inject/                    # Context-based dependency injection
│   └── inject.go              # WithX/From helpers for DB, Logger, HTTPClient, AnalyzerURL
├── grpc/                      # gRPC service implementations
│   ├── server.go              # Service registration and gateway setup
│   ├── errors.go              # Shared error sentinels
│   ├── user_service.go        # User service implementation
│   ├── journal_service.go     # Journal service implementation
│   ├── analytics_service.go   # Analytics service implementation
│   ├── util_service.go        # Util service implementation
│   └── featureflag_service.go # Feature flag service implementation
├── db/                        # sqlc-generated database code
│   ├── db.go                  # Database connection
│   ├── querier.go             # Querier interface (generated)
│   ├── models.go              # Generated models
│   ├── users.sql.go           # Generated user queries
│   ├── journals.sql.go        # Generated journal queries
│   ├── journal_topics.sql.go  # Generated journal topics queries
│   ├── analytics.sql.go       # Generated analytics queries
│   ├── feature_flags.sql.go   # Generated feature flag queries
│   └── runtime_config.sql.go  # Generated runtime config queries
├── mocks/                     # moq-generated mock implementations
│   ├── querier_mock.go        # Mock for db.Querier
│   └── http_client_mock.go    # Mock for inject.HTTPDoer (external HTTP calls)
├── pb/                        # buf-generated protobuf code
│   └── proto/
│       ├── user/              # User service proto definitions
│       ├── journal/           # Journal service proto definitions
│       ├── analytics/         # Analytics service proto definitions
│       ├── util/              # Util service proto definitions
│       └── featureflag/       # Feature flag service proto definitions
├── sql/                       # SQL queries (input for sqlc)
│   ├── queries/               # SQL query files
│   └── schema/                # Database schema migrations
└── utils/                     # Utility functions
```

## Key Patterns

### gRPC Service Implementation

Services use context-based dependency injection via the `inject` package. Dependencies (DB, Logger, HTTPClient, AnalyzerURL) are populated by an interceptor in `main.go` and extracted in handlers:

```go
type UserServer struct {
    pb.UnimplementedUserServiceServer
}

func (s *UserServer) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.CreateUserResponse, error) {
    logger := inject.LoggerFrom(ctx)
    dbq := inject.DBFrom(ctx)
    // Use dbq and logger in implementation
}
```

- Services are empty structs; dependencies come from `context.Context`
- Use `inject.DBFrom(ctx)`, `inject.LoggerFrom(ctx)`, `inject.HTTPClientFrom(ctx)`, `inject.AnalyzerURLFrom(ctx)` in handlers
- Tests build a context with `inject.WithDB(ctx, mockQuerier)` and `inject.WithLogger(ctx, logger)` via `testCtx()`

### Logging

- Use `log/slog` with JSON output
- Structured logging with key-value pairs
- Log errors with context before returning gRPC errors
- gRPC interceptor logs all requests with duration

### Error Handling

- Return proper gRPC status codes:
  - `codes.Internal` - Server errors
  - `codes.InvalidArgument` - Invalid input
  - `codes.NotFound` - Resource not found
  - `codes.AlreadyExists` - Duplicate resources
- Use `status.Errorf()` to create errors with codes
- Always log errors before returning

### Database Access

- Use sqlc-generated queries from `internal/db`
- Never write raw SQL in Go code - use sqlc queries
- Database access is obtained via `inject.DBFrom(ctx)` (returns `db.Querier`)
- Use `context.Context` for all database operations

### External Service Communication

- Journal service calls Analyzer service via HTTP
- Use `http.Client` with timeout (10 seconds)
- Analyzer URL comes from `ANALYZER_BASE_URL` environment variable
- Handle HTTP errors gracefully

## Testing

### Test Structure

- Unit tests: `*_test.go` files alongside source code (use `grpc_test` package for external tests)
- Integration tests: `*_integration_test.go` files
- Use `testify` for assertions and test suites
- Use `moq` for generating mock implementations
- Use `internal/testfixtures` for integration-test database setup when a supported model exists

### Running Tests

```bash
# From service directory
go test ./...

# With verbose output
go test -v ./...

# Run only unit tests (with mocks, no DB required)
go test -v ./internal/grpc/... -run "TestUserServer_|TestJournalServer_"

# Run specific test
go test -v ./internal/grpc -run TestUserService
```

### Mocking with moq

The codebase uses [moq](https://github.com/matryer/moq) for generating mock implementations. Generated mocks are in `internal/mocks/`:

- `QuerierMock` - Mock for `db.Querier` (database operations)
- `HTTPDoerMock` - Mock for `inject.HTTPDoer` (external HTTP calls)

Example test using mocks:

```go
package grpc_test

import (
    "context"
    "testing"

    "github.com/google/uuid"
    "github.com/jyablonski/lotus/internal/db"
    internalgrpc "github.com/jyablonski/lotus/internal/grpc"
    "github.com/jyablonski/lotus/internal/inject"
    "github.com/jyablonski/lotus/internal/mocks"
    "github.com/stretchr/testify/assert"
)

func testCtx(mock db.Querier) context.Context {
    ctx := context.Background()
    ctx = inject.WithDB(ctx, mock)
    ctx = inject.WithLogger(ctx, newTestLogger())
    return ctx
}

func TestUserServer_GetUser_Success(t *testing.T) {
    mockQuerier := &mocks.QuerierMock{
        GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
            return db.SourceUser{ID: uuid.New(), Email: email}, nil
        },
    }

    server := &internalgrpc.UserServer{}
    resp, err := server.GetUser(testCtx(mockQuerier), req)

    assert.NoError(t, err)
    assert.Len(t, mockQuerier.GetUserByEmailCalls(), 1)
}
```

### Regenerating Mocks

```bash
# From repository root
make moq-generate

# Or directly
./scripts/moq-generate.sh
```

Mocks are automatically regenerated via pre-commit hook when `internal/db/querier.go` or `internal/inject/inject.go` change (see `.pre-commit-config.yaml`).

### Integration Test Infrastructure

Shared integration infrastructure lives in `internal/testinfra`.

- `testinfra.Setup(ctx, schemaDir)` starts a `pgvector/pgvector:pg16` PostgreSQL container, applies goose migrations from `internal/sql/schema`, runs River migrations, starts Redis, and returns a `*testinfra.TestDB`.
- `TestDB` exposes `Pool *pgxpool.Pool`, `ConnStr`, an insert-only `RiverClient`, and a `RedisClient`.
- `testinfra.ApplyExtraSQL` loads extra SQL fixtures, such as dbt-managed schemas used by analytics tests.
- `testinfra.MockAnalyzerServer(t)` and `testinfra.FailingAnalyzerServer(t)` create analyzer HTTP test servers and register cleanup automatically.

Package-level `TestMain` functions in `internal/grpc` and `internal/jobs` start the shared containers once per package test run. Most gRPC integration tests call `newTestCtx(t)`, which begins a pgx transaction, wraps it with `db.New(tx)`, injects the query object into context, and rolls the transaction back with `t.Cleanup`.

Use `newDirectQueries(t)` only when the code under test commits outside the test transaction and the test needs to observe committed rows.

### Fixture Helpers

Database fixture helpers live in `internal/testfixtures`. Prefer them over hand-written `Create*Params`, upsert params, or raw SQL for supported setup records.

Supported models:

- `db.SourceUser`
- `db.SourceJournal`
- `db.SourceUserGameBalance`
- `db.SourceUserGameBet`
- `db.SourceJournalExport`
- `db.SourceJournalCommunityProjection`
- `db.SourceCommunityThemeRollup`
- `db.SourceCommunityMoodRollup`
- `db.SourceCommunitySummary`
- `db.SourceCommunityPromptSet`
- `db.SourceRuntimeConfig`

Primary API:

```go
user := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceUser{})
journal := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceJournal{
    UserID:      user.ID,
    JournalText: "A test journal entry",
    MoodScore:   testfixtures.Int32Ptr(7),
})
```

- `BuildDefaultModel(t, model)` returns defaults without persisting.
- `Create(t, ctx, queries, model)` persists an already-populated supported model.
- `CreateWithDefaults(t, ctx, queries, model, fieldsToEmpty...)` merges non-zero caller fields over defaults, resolves supported foreign keys, and persists.
- `fieldsToEmpty` takes validated Go struct field names, e.g. `"MoodScore"`, for cases where a default is non-zero but the test needs the zero value.
- FK-aware fixtures create parent users/journals when required IDs are omitted and respect existing FK values when supplied.
- Community rollup `DeltaVsPrevious` defaults to invalid/NULL. Pass `testfixtures.Numeric(t, "0")` when a test needs a real numeric zero.

Raw SQL is still acceptable in tests for unsupported models or specialized database types, such as journal sentiments, journal topics, and pgvector embeddings.

### Test Patterns

- Use table-driven tests for multiple test cases
- Mock external dependencies (HTTP clients, etc.)
- Validation-only tests should use `context.Background()` and avoid DB setup
- Integration tests should use `newTestCtx(t)` plus `testfixtures` for supported database setup
- Unit tests should keep explicit mocked sqlc params when those params are part of the behavior being asserted

## Configuration

### Environment Variables

- `DB_CONN` - PostgreSQL connection string (required)
  - Format: `postgres://user:password@host:port/dbname?sslmode=disable`
- `ANALYZER_BASE_URL` - Analyzer service URL (default: `http://localhost:8083`)

### Database Schema

- Schema files: `internal/sql/schema/`
- Migrations are managed by Django (see `services/django/`)
- Schema changes require:
  1. Update SQL schema files
  2. Run migrations via Django
  3. Update sqlc queries if needed
  4. Regenerate sqlc code

## Key Files to Understand

Before making changes:

1. `internal/main.go` - Entry point, server startup
2. `internal/grpc/server.go` - gRPC server setup and interceptors
3. `internal/grpc/journal_service.go` - Example service implementation
4. `internal/db/` - Generated database code (read-only, regenerated)
5. `internal/sql/queries/` - SQL queries (input for sqlc)
6. `proto/` - Protobuf definitions (input for buf)
7. `sqlc.yaml` - sqlc configuration
8. `buf.yaml` / `buf.gen.yaml` - buf configuration

## Common Tasks

### Adding a New gRPC Service

1. Define proto file in `proto/{service_name}/{service_name}.proto`
2. Run `make buf-generate` to generate Go code
3. Create service implementation in `internal/grpc/{service_name}_service.go` (use `inject` for dependencies)
4. Register service in `internal/grpc/server.go` (`RegisterServices` and `RegisterGateway`)
5. Add SQL queries in `internal/sql/queries/` if needed
6. Run `make sqlc-generate` if SQL changed

### Adding a New Database Query

1. Add SQL query to `internal/sql/queries/{domain}.sql`
2. Follow sqlc query format (see existing queries)
3. Run `make sqlc-generate`
4. Use generated function in service code

### Modifying Proto Definitions

1. Edit proto file in `proto/{service}/{service}.proto`
2. Run `make buf-generate`
3. Update service implementation to match new proto
4. Update gateway registration if needed

### Debugging

- Check logs for structured JSON output
- gRPC interceptor logs all requests with duration
- Use `grpcurl` or Postman for testing gRPC endpoints
- Test HTTP gateway at `http://localhost:8080`

## Code Style

- Follow standard Go formatting (`go fmt`)
- Use `golangci-lint` if configured
- Use meaningful variable names
- Keep functions focused and single-purpose
- Use context.Context for cancellation and timeouts
- Handle errors explicitly (no silent failures)

## Pre-commit Hooks

- `sqlc-generate` runs automatically when SQL files change
- `buf-generate` runs automatically when proto files change
- `moq-generate` runs automatically when interface files change
- `go-fmt` runs for Go files

## Deployment

- Uses `Dockerfile.dev` for development (with Air)
- Uses `Dockerfile` for production builds
- Ports exposed: 8080 (gRPC-Gateway), 50051 (gRPC)
