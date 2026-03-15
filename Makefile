# set the default make command to 'help'
.DEFAULT_GOAL := help

.PHONY: up
up: ## Start all services in detached mode
	@tilt up

.PHONY: down
down: ## Stop and remove all services
	@tilt down

.PHONY: start-postgres
start-postgres: ## Start only the PostgreSQL service
	@docker compose -f docker/docker-compose-local.yaml up -d postgres

.PHONY: stop-postgres
stop-postgres: ## Stop only the PostgreSQL service
	@docker compose -f docker/docker-compose-local.yaml down postgres

.PHONY: ci-analyzer-up
ci-analyzer-up: ## Start dependencies for analyzer CI (PostgreSQL and MLflow)
	@docker compose -f docker/docker-compose-local.yaml --profile analyzer up -d postgres mlflow

.PHONY: ci-analyzer-down
ci-analyzer-down: ## Stop dependencies for analyzer CI (PostgreSQL and MLflow)
	@docker compose -f docker/docker-compose-local.yaml --profile analyzer down postgres mlflow

.PHONY: test-analyzer
test-analyzer: ## Run analyzer tests with coverage (testcontainers spins up an isolated Postgres automatically)
	@cd services/analyzer && uv run pytest

.PHONY: test-backend
test-backend: ## Run backend tests with coverage (testcontainers spins up an isolated Postgres automatically)
	@cd services/backend && go tool gotestsum --format testdox -- ./... -coverprofile=/tmp/backend-coverage.out -covermode=atomic -coverpkg=./internal/grpc,./internal/http,./internal/utils && go tool cover -func=/tmp/backend-coverage.out; rm -f /tmp/backend-coverage.out

.PHONY: sqlc-generate
sqlc-generate: ## Generate Go code from SQL using sqlc
	@cd services/backend && sqlc generate

.PHONY: buf-generate
buf-generate: ## Generate protobuf/grpc code using buf
	@cd services/backend && buf generate

.PHONY: moq-generate
moq-generate: ## Generate Go mocks using moq
	@./scripts/moq-generate.sh

.PHONY: bruno-generate
bruno-generate: ## Generate Bruno API collection from OpenAPI specs
	@./scripts/bruno-generate.sh

.PHONY: generate
generate: sqlc-generate buf-generate moq-generate ## Run all code generation (sqlc, buf, moq)

.PHONY: e2e-up
e2e-up: ## Start e2e stack (postgres, backend, frontend)
	@docker compose -f docker/docker-compose-e2e.yaml up -d --build

.PHONY: e2e-down
e2e-down: ## Stop e2e stack and remove volumes
	@docker compose -f docker/docker-compose-e2e.yaml down -v

.PHONY: e2e-test
e2e-test: ## Run Playwright e2e tests (stack must be running)
	@cd services/frontend && npx playwright test

.PHONY: pact-broker-up
pact-broker-up: ## Start the Pact Broker
	@docker compose -f docker/docker-compose-local.yaml --profile pact up -d pact-broker

.PHONY: pact-broker-down
pact-broker-down: ## Stop the Pact Broker
	@docker compose -f docker/docker-compose-local.yaml --profile pact down pact-broker

.PHONY: help
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  %-16s %s\n", $$1, $$2}'
