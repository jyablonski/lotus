# Backend Service - Agent Guide

Go gRPC service with HTTP gateway for core application logic, CRUD operations, and API gateway functionality.

## Technology Stack

- **Language**: Go 1.25.4
- **Framework**: gRPC with grpc-gateway for HTTP
- **Database**: PostgreSQL
- **Code Generation**: sqlc (SQL → Go), buf (protobuf → Go), moq (mocks)
- **Hot Reload**: Air (development only)
- **Testing**: testify, moq

## Architecture Patterns

### Service Structure

The backend runs **three servers** concurrently:

1. **gRPC Server** (`:50051`) - Core gRPC service
2. **HTTP Server** (`:8081`) - Legacy HTTP endpoints (deprecated)
3. **gRPC-Gateway** (`:8080`) - HTTP gateway that translates HTTP → gRPC

### Code Generation

The service uses **code generation** for type safety:

- **sqlc** - Generates Go code from SQL queries
  - SQL files: `internal/sql/queries/`
  - Generated code: `internal/db/`
  - Config: `sqlc.yaml`
  - Run: `make sqlc-generate` or `cd services/backend && sqlc generate`

- **buf** - Generates gRPC/protobuf code
  - Proto files: `proto/`
  - Generated code: `internal/pb/proto/`
  - Config: `buf.yaml`, `buf.gen.yaml`
  - Run: `make buf-generate` or `cd services/backend && buf generate`

- **moq** - Generates mock implementations for interfaces
  - Interfaces: `internal/db/querier.go`, `internal/grpc/interfaces.go`
  - Generated mocks: `internal/mocks/`
  - Run: `make moq-generate` or `./scripts/moq-generate.sh`

**Important**: Always regenerate code after changing SQL queries or proto definitions.

## Code Organization

```
internal/
├── main.go                    # Entry point, starts all three servers
├── grpc/                      # gRPC service implementations
│   ├── server.go              # gRPC server setup and interceptors
│   ├── interfaces.go          # Interface definitions (HTTPClient)
│   ├── user_service.go        # User service implementation
│   ├── journal_service.go     # Journal service implementation
│   └── analytics_service.go   # Analytics service implementation
├── http/                      # Legacy HTTP handlers (deprecated)
│   ├── server.go
│   └── user_handler.go
├── db/                        # sqlc-generated database code
│   ├── db.go                  # Database connection
│   ├── querier.go             # Querier interface (generated)
│   ├── models.go              # Generated models
│   ├── users.sql.go           # Generated user queries
│   ├── journals.sql.go        # Generated journal queries
│   └── analytics.sql.go       # Generated analytics queries
├── mocks/                     # moq-generated mock implementations
│   ├── querier_mock.go        # Mock for db.Querier
│   └── http_client_mock.go    # Mock for grpc.HTTPClient
├── pb/                        # buf-generated protobuf code
│   └── proto/
│       ├── user/              # User service proto definitions
│       ├── journal/           # Journal service proto definitions
│       └── analytics/         # Analytics service proto definitions
├── sql/                       # SQL queries (input for sqlc)
│   ├── queries/               # SQL query files
│   └── schema/                # Database schema migrations
└── utils/                     # Utility functions
```

## Key Patterns

### gRPC Service Implementation

Each gRPC service follows this pattern:

```go
type ServiceServer struct {
    pb.UnimplementedServiceServer
    DB     db.Querier   // Interface, not concrete *db.Queries
    Logger *slog.Logger
    // ... other dependencies
}

func (s *ServiceServer) Method(ctx context.Context, req *pb.Request) (*pb.Response, error) {
    // Implementation
}
```

Services use interfaces for dependencies to enable mocking in tests.

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

- Use **sqlc-generated** queries from `internal/db`
- Never write raw SQL in Go code - use sqlc queries
- Database connection is passed to services via `*db.Queries`
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
- `HTTPClientMock` - Mock for `grpc.HTTPClient` (external HTTP calls)

Example test using mocks:

```go
package grpc_test

import (
    "context"
    "testing"

    "github.com/jyablonski/lotus/internal/db"
    internalgrpc "github.com/jyablonski/lotus/internal/grpc"
    "github.com/jyablonski/lotus/internal/mocks"
)

func TestUserServer_GetUser_Success(t *testing.T) {
    // Configure mock behavior
    mockQuerier := &mocks.QuerierMock{
        GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
            return db.SourceUser{
                ID:    uuid.New(),
                Email: email,
            }, nil
        },
    }

    // Create service with mock
    server := internalgrpc.UserService(mockQuerier, newTestLogger())

    // Test the service
    resp, err := server.GetUser(context.Background(), req)

    // Verify mock was called
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

Mocks are automatically regenerated via pre-commit hook when `internal/db/querier.go` or `internal/grpc/interfaces.go` change.

### Test Patterns

- Use table-driven tests for multiple test cases
- Mock external dependencies (HTTP clients, etc.)
- Integration tests require PostgreSQL running

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

1. **`internal/main.go`** - Entry point, server startup
2. **`internal/grpc/server.go`** - gRPC server setup and interceptors
3. **`internal/grpc/journal_service.go`** - Example service implementation
4. **`internal/db/`** - Generated database code (read-only, regenerated)
5. **`internal/sql/queries/`** - SQL queries (input for sqlc)
6. **`proto/`** - Protobuf definitions (input for buf)
7. **`sqlc.yaml`** - sqlc configuration
8. **`buf.yaml`** / `buf.gen.yaml` - buf configuration

## Common Tasks

### Adding a New gRPC Service

1. Define proto file in `proto/{service_name}/{service_name}.proto`
2. Run `make buf-generate` to generate Go code
3. Create service implementation in `internal/grpc/{service_name}_service.go`
4. Register service in `internal/grpc/server.go`
5. Register gateway handler in `internal/main.go`
6. Add SQL queries in `internal/sql/queries/` if needed
7. Run `make sqlc-generate` if SQL changed

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
- Ports exposed: 8080 (gateway), 8081 (legacy HTTP), 50051 (gRPC)
- Health check endpoint: `:8081/health`
