.PHONY: up
up:
	@docker compose -f docker/docker-compose-local.yaml up

.PHONY: down
down:
	@docker compose -f docker/docker-compose-local.yaml down

.PHONY: start-postgres
start-postgres:
	@docker compose -f docker/docker-compose-postgres.yaml -d up

.PHONY: stop-postgres
stop-postgres:
	@docker compose -f docker/docker-compose-postgres.yaml down
