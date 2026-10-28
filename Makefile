.PHONY: help up up-box up-worker up-fem up-fem-box down down-box logs ps restart smoke stress stress-jobs health health-box build

COMPOSE ?= docker compose
ENV_FILE ?= .env
COMPOSE_BOX := $(COMPOSE) -f docker-compose.yml -f docker-compose.box.yml

help:
	@echo "Targets: up up-box up-worker up-fem up-fem-box build down down-box logs ps restart smoke stress stress-jobs health health-box"
	@echo "  stress     — curl parallel GET /health (scripts/stress-smoke.sh; Q4-10)"
	@echo "  stress-jobs — analytic/fem dry-run enqueue+poll (scripts/stress-jobs.sh; Q4-10)"
	@echo "  up         — default 4 services (service DNS postgres/redis)"
	@echo "  up-box     — Bot/box iptables-stub smoke (host.docker.internal)"
	@echo "  up-worker  — + Celery worker profile (CELERY_ENABLED=1)"
	@echo "  up-fem     — + analytic worker + fem toolchain + worker-fem (normal Docker DNS)"
	@echo "  up-fem-box — same as up-fem with box overlay (host.docker.internal)"

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
	@echo "[mo] up-fem: profiles worker,fem (toolchain + worker-fem; arch 8d966d9)"
	CELERY_ENABLED=1 $(COMPOSE) --env-file $(ENV_FILE) --profile worker --profile fem up -d --build
	@$(MAKE) --no-print-directory health || true


up-fem-box:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-fem-box: box overlay + profiles worker,fem (Q3-L2 Elmer)"
	CELERY_ENABLED=1 $(COMPOSE_BOX) --env-file $(ENV_FILE) --profile worker --profile fem up -d --build
	@$(MAKE) --no-print-directory health-box || true

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

stress:
	bash scripts/stress-smoke.sh

stress-jobs:
	bash scripts/stress-jobs.sh

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
