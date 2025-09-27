# set the default make command to 'help'
.DEFAULT_GOAL := help

.PHONY: up
up:
	@docker compose -f docker/docker-compose-local.yaml up -d

.PHONY: down
down:
	@docker compose -f docker/docker-compose-local.yaml down

.PHONY: build
build:
	@docker compose -f docker/docker-compose-local.yaml build

.PHONY: start-postgres
start-postgres:
	@docker compose -f docker/docker-compose-local.yaml up -d postgres

.PHONY: stop-postgres
stop-postgres:
	@docker compose -f docker/docker-compose-local.yaml down postgres

.PHONY: ci-analyzer-up
ci-analyzer-up:
	@docker compose -f docker/docker-compose-local.yaml up -d postgres mlflow

.PHONY: ci-analyzer-down
ci-analyzer-down:
	@docker compose -f docker/docker-compose-local.yaml down postgres mlflow

.PHONY: sqlc-generate
sqlc-generate:
	@cd services/backend && sqlc generate

.PHONY: buf-generate
buf-generate:
	@cd services/backend && buf generate

.PHONY: generate
generate: sqlc-generate buf-generate

.PHONY: help
help:
	@echo "Available targets:"
	@echo ""
	@echo "Docker Management:"
	@echo "  up             - Start all services"
	@echo "  down           - Stop all services"
	@echo "  build          - Build all Docker images"
	@echo ""
	@echo "Database:"
	@echo "  start-postgres - Start PostgreSQL only"
	@echo "  stop-postgres  - Stop PostgreSQL only"
	@echo ""
	@echo "CI:"
	@echo "  ci-analyzer-up   - Start PostgreSQL and MLflow"
	@echo "  ci-analyzer-down - Stop PostgreSQL and MLflow"
	@echo ""
	@echo "Backend SQLC + Protobuf Generation:"
	@echo "  generate       - Generate all code (SQL + protobuf)"
	@echo "  sqlc-generate  - Generate SQL code only"
	@echo "  buf-generate   - Generate protobuf code only"
	@echo ""
	@echo "  help           - Show this help message"
