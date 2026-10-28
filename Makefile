.PHONY: help up down logs ps restart smoke

COMPOSE ?= docker compose
ENV_FILE ?= .env

help:
	@echo "Targets: up down logs ps restart smoke"

up:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	$(COMPOSE) --env-file $(ENV_FILE) up -d

down:
	$(COMPOSE) --env-file $(ENV_FILE) down

logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f

ps:
	$(COMPOSE) --env-file $(ENV_FILE) ps

restart:
	$(COMPOSE) --env-file $(ENV_FILE) restart

smoke:
	bash scripts/smoke.sh
