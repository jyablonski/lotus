# Lotus Monorepo - Agent Guide

This document provides high-level guidance for AI agents working in the Lotus monorepo. For service-specific patterns and conventions, see the `AGENTS.md` file in each service directory.

## Architecture Overview

Lotus is a full-stack journal application with ML/LLM-powered topic classification and sentiment analysis. The monorepo uses a microservices architecture with the following services:

### Service Communication Flow

```
Frontend (Next.js)
  → HTTP → Go gRPC Gateway (:8080)
    → gRPC → Go Backend Service (:50051)
      → PostgreSQL Database
      → HTTP → Analyzer Service (:8083)
        → MLflow (Model Registry)
        → OpenAI API
```

### Core Services

- **Frontend** (`services/frontend/`) - Next.js 15 with React 19, TypeScript, Tailwind CSS
- **Backend** (`services/backend/`) - Go gRPC service with HTTP gateway
- **Analyzer** (`services/analyzer/`) - FastAPI service for ML/LLM model inference
- **Django Admin** (`services/django/`) - Database migrations and admin interface
- **Dagster** (`services/dagster/`) - Data orchestration and pipeline management
- **dbt** (`services/dbt/`) - Data transformation and modeling
- **Experiments** (`services/experiments/`) - ML model training and MLflow integration

### Infrastructure Services

- **PostgreSQL** - Primary database (port 5432)
- **Redis** - Caching and task queue (port 6379)
- **MLflow** - Model registry and experiment tracking (port 5000)

## Monorepo Tooling

### Tilt (Primary Development Tool)

**Tilt** is the primary tool for local development. It provides:

- Automatic rebuilds on file changes
- Smart dependency caching
- Unified UI for logs and service status
- Hot-reloading for faster iteration

**Usage:**

```bash
make up      # Start all services via Tilt
make down    # Stop all services
```

**Configuration:** `tilt_config.yaml` controls which services are enabled. Changes are picked up automatically without restarting Tilt.

**Service URLs:**

- Tilt UI: http://localhost:10350
- Frontend: http://localhost:3000
- Backend Gateway: http://localhost:8080
- Backend gRPC: http://localhost:50051
- Analyzer: http://localhost:8083
- Django Admin: http://localhost:8000/admin/
- MLflow UI: http://localhost:5000
- Dagster UI: http://localhost:3001

### Docker Compose

Used as a fallback and for CI/CD:

- `docker/docker-compose-local.yaml` - Local development configuration
- `docker/docker-compose-tilt.yaml` - Tilt-specific overrides

### Code Generation

The backend service uses code generation tools:

- **sqlc** - Generates Go code from SQL queries (`make sqlc-generate`)
- **buf** - Generates protobuf/gRPC code (`make buf-generate`)
- **make generate** - Runs both generators

These are automatically run via pre-commit hooks when SQL or proto files change.

## Cross-Cutting Concerns

### Logging

- **Go services**: Use `log/slog` with JSON output
- **Python services**: Use Python `logging` module with structured logging
- **Frontend**: Console logging for development, structured logging for production

### Error Handling

- **gRPC**: Return proper gRPC status codes (`codes.Internal`, `codes.InvalidArgument`, etc.)
- **HTTP**: Use standard HTTP status codes
- **FastAPI**: Use HTTPException with appropriate status codes
- Always log errors with context before returning

### Observability

- Structured logging is the primary observability mechanism
- All services log in JSON format for easy parsing
- gRPC services include request duration and method in logs

### Environment Variables

Each service has its own environment configuration. Common patterns:

- Database connection strings use `DB_CONN` or service-specific variants
- Service URLs use `{SERVICE}_BASE_URL` pattern (e.g., `ANALYZER_BASE_URL`)
- Secrets are loaded from `.env` files (not committed to git)

## Code Quality & Linting

### Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:

- **Go**: `go-fmt` for formatting
- **Python**: `ruff` for linting and formatting (excludes `services/airflow/`)
- **Frontend**: `prettier` for formatting
- **YAML**: `yamllint` for validation
- **Shell**: `shellcheck` for script validation
- **General**: trailing whitespace, end-of-file fixes, large file checks

### Python Standards

Root `pyproject.toml` defines shared Python standards:

- **Ruff** for linting and formatting
- Line length: 100 characters
- Target Python version: 3.13
- Import sorting with `isort`
- Comprehensive lint rules (E, W, F, I, B, C4, UP, ARG, SIM, TCH, PIE, PT, RUF)

### Go Standards

- Use `go fmt` for formatting
- Follow standard Go project layout
- Use `sqlc` for type-safe database queries

### TypeScript/JavaScript Standards

- ESLint with Next.js config
- Prettier for formatting
- TypeScript strict mode

## Testing Expectations

### Python Services

- Use `pytest` for all Python services
- Test files should be in `tests/` directory
- Use `pytest-cov` for coverage reporting
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

### Go Services

- Use standard Go testing package
- Integration tests use `*_integration_test.go` naming
- Use `testify` for assertions

### Frontend

- Use Jest with React Testing Library
- Test files: `__tests__/` directory or `*.test.tsx` files
- Run with `npm test` or `npm run test:watch`

## CI/CD

Each service has its own GitHub Actions workflow in `.github/workflows/`:

- `analyzer.yaml` - Analyzer service tests
- `backend.yaml` - Backend service tests
- `dagster.yaml` - Dagster service tests
- `dbt.yaml` - dbt service tests
- `django.yaml` - Django service tests
- `experiments.yaml` - Experiments service tests
- `frontend.yaml` - Frontend service tests

Workflows run tests and linting on pull requests.

## PR & Commit Conventions

### Pull Requests

Use the template in `.github/pull_request_template.md`:

- Description of changes
- Sections: Added, Updated, Deleted

### Commit Messages

- Use clear, descriptive commit messages
- Reference issues/PRs when applicable
- Pre-commit hooks will validate formatting

## Directory Structure

```
lotus/
├── .github/workflows/     # CI/CD workflows (one per service)
├── docker/                # Docker Compose configs and DB bootstrap scripts
├── services/              # All application services
│   ├── analyzer/          # FastAPI ML inference service
│   ├── backend/           # Go gRPC backend service
│   ├── dagster/          # Dagster orchestration
│   ├── dbt/              # dbt transformations
│   ├── django/           # Django admin and migrations
│   ├── experiments/      # ML model training
│   └── frontend/         # Next.js frontend
├── scripts/              # Shared scripts (sqlc, buf generation)
├── Makefile             # Common make targets
├── Tiltfile             # Tilt configuration
├── tilt_config.yaml     # Service enable/disable config
└── pyproject.toml        # Root Python standards (Ruff config)
```

## Service Deployment Mapping

Each service in `services/` maps to a deployed service:

- `services/frontend/` → Frontend web application
- `services/backend/` → Backend gRPC/HTTP API
- `services/analyzer/` → ML inference API
- `services/django/` → Admin interface and migrations
- `services/dagster/` → Data orchestration service
- `services/dbt/` → Data transformation jobs (run via Dagster)
- `services/experiments/` → ML training jobs (not deployed, used for training)

## Key Files to Understand

Before making changes, familiarize yourself with:

- `README.md` - Project overview and architecture diagrams
- `Tiltfile` - How services are built and configured
- `tilt_config.yaml` - Which services are enabled
- `docker/docker-compose-local.yaml` - Service dependencies and networking
- `.pre-commit-config.yaml` - Code quality checks
- `pyproject.toml` - Python linting and formatting rules
- `Makefile` - Common development commands

## Notes

- **Airflow** is a legacy service and is excluded from most tooling (ruff, etc.)
- **Dagster** is the preferred orchestration tool over Airflow
- All Python services use **uv** for dependency management
- Services use **Docker** for containerization
- Development uses **hot-reloading** where possible (Air for Go, Next.js dev server, etc.)
