.PHONY: help up up-box down down-box logs ps restart smoke health health-box build

COMPOSE ?= docker compose
ENV_FILE ?= .env
COMPOSE_BOX := $(COMPOSE) -f docker-compose.yml -f docker-compose.box.yml

help:
	@echo "Targets: up up-box build down down-box logs ps restart smoke health health-box"
	@echo "  up      — default (service DNS postgres/redis) for normal Docker"
	@echo "  up-box  — Bot/box iptables-stub smoke (api via host.docker.internal:5433/6380)"

up:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	$(COMPOSE) --env-file $(ENV_FILE) up -d --build
	@$(MAKE) --no-print-directory health || true

up-box:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-box: overlay docker-compose.box.yml (host.docker.internal deps)"
	$(COMPOSE_BOX) --env-file $(ENV_FILE) up -d --build
	@$(MAKE) --no-print-directory health-box || true

build:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	$(COMPOSE) --env-file $(ENV_FILE) build

down:
	$(COMPOSE) --env-file $(ENV_FILE) down

down-box:
	$(COMPOSE_BOX) --env-file $(ENV_FILE) down

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

health-box:
	@echo "== compose ps (box) =="
	@$(COMPOSE_BOX) --env-file $(ENV_FILE) ps
	@echo "== GET /health (box) =="
	@curl -sf http://127.0.0.1:$${API_HOST_PORT:-8000}/health | python3 -m json.tool
