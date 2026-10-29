.PHONY: help up up-box up-worker up-fem up-fem-box down down-box logs ps restart smoke stress stress-jobs health health-box assert-box build

COMPOSE ?= docker compose
ENV_FILE ?= .env
COMPOSE_BOX := $(COMPOSE) -f docker-compose.yml -f docker-compose.box.yml

help:
	@echo "Targets: up up-box up-worker up-fem up-fem-box build down down-box logs ps restart smoke stress stress-jobs health health-box assert-box"
	@echo "  stress     — curl parallel GET /health (scripts/stress-smoke.sh; Q4-10)"
	@echo "  stress-jobs — analytic/fem dry-run enqueue+poll (scripts/stress-jobs.sh; Q4-10)"
	@echo "  up         — default 4 services (service DNS postgres/redis) 【非 box】"
	@echo "  up-box     — Bot/box：双文件 overlay（host.docker.internal）；禁后接裸 compose up"
	@echo "  up-worker  — + Celery worker profile（非 box；box 请用 up-fem-box 或双文件 recreate）"
	@echo "  up-fem     — + analytic worker + fem toolchain + worker-fem（非 box）"
	@echo "  up-fem-box — box overlay + worker + fem（api/web/worker/worker-fem 全带 overlay）"
	@echo "  assert-box — 检查运行态是否仍挂 docker-compose.box.yml（防漂）"
	@echo "  脚本等价：./scripts/up-box.sh  ./scripts/up-fem-box.sh  ./scripts/assert-box-overlay.sh"

up:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up: 单文件 docker-compose.yml（服务 DNS）。Bot/box 请改用 make up-box / up-fem-box"
	$(COMPOSE) --env-file $(ENV_FILE) up -d --build
	@$(MAKE) --no-print-directory health || true

up-box:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-box: 双文件 docker-compose.yml + docker-compose.box.yml"
	@echo "[mo] 防漂：此后禁止裸 docker compose up / scripts/start-deps.sh（会覆盖 overlay → :5174 代理挂死）"
	$(COMPOSE_BOX) --env-file $(ENV_FILE) up -d --build
	@$(MAKE) --no-print-directory health-box || true
	@bash scripts/assert-box-overlay.sh || true

up-worker:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-worker: profile worker + CELERY_ENABLED=1（非 box）"
	@echo "[mo] 若当前是 box 栈：勿用本目标；改用 make up-fem-box 或双文件 --force-recreate worker"
	CELERY_ENABLED=1 $(COMPOSE) --env-file $(ENV_FILE) --profile worker up -d --build
	@$(MAKE) --no-print-directory health || true

up-fem:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-fem: profiles worker,fem（toolchain + worker-fem; arch 8d966d9）【非 box】"
	@echo "[mo] Bot/box 请用 make up-fem-box，否则 worker 会漂回 postgres/redis DNS"
	CELERY_ENABLED=1 $(COMPOSE) --env-file $(ENV_FILE) --profile worker --profile fem up -d --build
	@$(MAKE) --no-print-directory health || true

up-fem-box:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "[mo] up-fem-box: 双文件 overlay + profiles worker,fem（Q3-L2 Elmer；默认 MO_FEM_DRY_RUN=1）"
	@echo "[mo] 防漂：api/web/worker/worker-fem 均须带 box；禁止事后裸 compose --profile worker|fem up"
	CELERY_ENABLED=1 $(COMPOSE_BOX) --env-file $(ENV_FILE) --profile worker --profile fem up -d --build
	@$(MAKE) --no-print-directory health-box || true
	@bash scripts/assert-box-overlay.sh || true

assert-box:
	@bash scripts/assert-box-overlay.sh

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
