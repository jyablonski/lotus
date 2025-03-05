.PHONY: up
up:
	@docker compose -f docker/docker-compose-postgres.yaml up -d postgres

.PHONY: down
down:
	@docker compose -f docker/docker-compose-postgres.yaml down