.PHONY: help up down logs ps restart smoke health build

COMPOSE ?= docker compose
ENV_FILE ?= .env

help:
	@echo "Targets: up build down logs ps restart smoke health"

up:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	$(COMPOSE) --env-file $(ENV_FILE) up -d --build
	@$(MAKE) --no-print-directory health || true

build:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	$(COMPOSE) --env-file $(ENV_FILE) build

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

health:
	@echo "== compose ps =="
	@$(COMPOSE) --env-file $(ENV_FILE) ps
	@echo "== GET /health =="
	@curl -sf http://127.0.0.1:$${API_HOST_PORT:-8000}/health | python3 -m json.tool
