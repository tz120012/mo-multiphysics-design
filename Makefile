.PHONY: help up up-box up-worker up-fem down down-box logs ps restart smoke health health-box build

COMPOSE ?= docker compose
ENV_FILE ?= .env
COMPOSE_BOX := $(COMPOSE) -f docker-compose.yml -f docker-compose.box.yml

help:
	@echo "Targets: up up-box up-worker up-fem build down down-box logs ps restart smoke health health-box"
	@echo "  up         — default 4 services (service DNS postgres/redis)"
	@echo "  up-box     — Bot/box iptables-stub smoke (host.docker.internal)"
	@echo "  up-worker  — + Celery worker profile (CELERY_ENABLED=1)"
	@echo "  up-fem     — + worker + fem stub (Q3-3 Elmer/GetDP placeholder)"

up:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	$(COMPOSE) --env-file $(ENV_FILE) up -d --build
	@$(MAKE) --no-print-directory health || true

up-box:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-box: overlay docker-compose.box.yml (host.docker.internal deps)"
	$(COMPOSE_BOX) --env-file $(ENV_FILE) up -d --build
	@$(MAKE) --no-print-directory health-box || true

up-worker:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-worker: profile worker + CELERY_ENABLED=1"
	CELERY_ENABLED=1 $(COMPOSE) --env-file $(ENV_FILE) --profile worker up -d --build
	@$(MAKE) --no-print-directory health || true

up-fem:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-fem: profiles worker,fem (Q3-3 stub)"
	CELERY_ENABLED=1 $(COMPOSE) --env-file $(ENV_FILE) --profile worker --profile fem up -d --build
	@$(MAKE) --no-print-directory health || true

build:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	$(COMPOSE) --env-file $(ENV_FILE) build

down:
	$(COMPOSE) --env-file $(ENV_FILE) --profile worker --profile fem down

down-box:
	$(COMPOSE_BOX) --env-file $(ENV_FILE) --profile worker --profile fem down

logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f

ps:
	$(COMPOSE) --env-file $(ENV_FILE) --profile worker --profile fem ps

restart:
	$(COMPOSE) --env-file $(ENV_FILE) restart

smoke:
	bash scripts/smoke.sh

health:
	@echo "== compose ps =="
	@$(COMPOSE) --env-file $(ENV_FILE) --profile worker --profile fem ps
	@echo "== GET /health =="
	@curl -sf http://127.0.0.1:$${API_HOST_PORT:-8000}/health | python3 -m json.tool

health-box:
	@echo "== compose ps (box) =="
	@$(COMPOSE_BOX) --env-file $(ENV_FILE) --profile worker --profile fem ps
	@echo "== GET /health (box) =="
	@curl -sf http://127.0.0.1:$${API_HOST_PORT:-8000}/health | python3 -m json.tool
