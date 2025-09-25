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
