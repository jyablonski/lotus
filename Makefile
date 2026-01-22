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

.PHONY: sqlc-generate
sqlc-generate: ## Generate Go code from SQL using sqlc
	@cd services/backend && sqlc generate

.PHONY: buf-generate
buf-generate: ## Generate protobuf/grpc code using buf
	@cd services/backend && buf generate

.PHONY: generate
generate: sqlc-generate buf-generate ## Run both sqlc and buf code generation

.PHONY: help
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  %-16s %s\n", $$1, $$2}'
