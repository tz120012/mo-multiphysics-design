#!/usr/bin/env bash
# One-click: web + api + Postgres + Redis（正常 Docker DNS）
# Bot/box（iptables-stub）：不要用本脚本 — 会裸 compose up，覆盖 docker-compose.box.yml，
# 导致 :5174 代理超时 / api·worker 解析不了 postgres·redis。请用：
#   make up-box / ./scripts/up-box.sh
#   make up-fem-box / ./scripts/up-fem-box.sh
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || cp .env.example .env
echo "[mo] start-deps.sh: 单文件 docker-compose.yml（非 box）。Bot/box 请改用 scripts/up-box.sh"
docker compose --env-file .env up -d --build
docker compose --env-file .env ps
echo
echo "Web:  http://127.0.0.1:${WEB_HOST_PORT:-5173}"
echo "API:  http://127.0.0.1:${API_HOST_PORT:-8000}/docs"
echo "Health: curl -s http://127.0.0.1:${API_HOST_PORT:-8000}/health"
echo "Postgres host: localhost:${POSTGRES_PORT:-5433}  Redis host: localhost:${REDIS_PORT:-6380}"
