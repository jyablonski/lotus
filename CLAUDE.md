# Lotus — Claude Code Guide

## Project Overview

Lotus is a full-stack journaling + analytics application with:

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind — `services/frontend`
- **Backend**: Go gRPC + grpc-gateway HTTP gateway — `services/backend`
- **Analyzer**: Python FastAPI for ML/NLP — `services/analyzer`
- **Data Pipeline**: Dagster + dbt — `services/dagster`, `services/dbt`
- **Infra**: Docker Compose at `docker/docker-compose-local.yaml`, Tilt for dev

## Quick Commands

```bash
# Start all services
make up

# Run backend tests (testcontainers — no external DB needed)
make test-backend

# Run analyzer tests
make test-analyzer

# Code generation
make sqlc-generate    # SQL → Go (services/backend)
make buf-generate     # protobuf → Go (services/backend)
make moq-generate     # interfaces → mocks (services/backend)

# Lint backend
cd services/backend && golangci-lint run ./...
```

## Backend Conventions (services/backend)

### Architecture

- gRPC server on `:50051`, HTTP gateway on `:8080`
- Context-based dependency injection via `internal/inject` package
- Services are empty structs; deps come from `inject.XFrom(ctx)`
- sqlc for DB queries (never write raw SQL in Go — add to `internal/sql/queries/`)
- River for background job queue (transactional enqueue with pgx)

### Testing

- Unit tests use moq-generated mocks (`internal/mocks/`)
- Integration tests use testcontainers (Postgres + Redis) — no external services needed
- Test transactions roll back on cleanup for isolation
- `TestMain` in each test package sets up shared containers

### Error Handling

- Return proper gRPC status codes (`codes.Internal`, `codes.NotFound`, etc.)
- Wrap errors with `fmt.Errorf("context: %w", err)` for chain
- Always log errors with structured slog before returning

### Code Generation

Always regenerate after changing:

- SQL queries → `make sqlc-generate`
- Proto definitions → `make buf-generate`
- Interfaces (`internal/inject/inject.go`, `internal/db/querier.go`) → `make moq-generate`

### Linting

- `golangci-lint` configured at `services/backend/.golangci.yml`
- Generated code (`internal/pb/`, `internal/mocks/`, `internal/db/`) is excluded
- Run `golangci-lint run ./...` from `services/backend/`

## Frontend Conventions (services/frontend)

### Architecture

- Next.js App Router with Server Actions
- Server Actions call backend directly via `http://backend:8080`
- OpenTelemetry with explicit traceparent injection in Server Actions

## General Rules

- Prefer editing existing files over creating new ones
- Don't add docstrings/comments to code you didn't change
- Keep PRs focused — one concern per PR
- All services run in Docker; `make up` starts everything via Tilt
