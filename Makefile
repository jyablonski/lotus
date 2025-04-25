.PHONY: up
up:
	@docker compose -f docker/docker-compose-local.yaml up

.PHONY: down
down:
	@docker compose -f docker/docker-compose-local.yaml down
