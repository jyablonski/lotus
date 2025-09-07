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
	@docker compose -f docker/docker-compose-postgres.yaml up -d

.PHONY: stop-postgres
stop-postgres:
	@docker compose -f docker/docker-compose-postgres.yaml down
