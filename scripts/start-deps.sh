#!/usr/bin/env bash
# One-click: web + api + Postgres + Redis
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || cp .env.example .env
docker compose --env-file .env up -d --build
docker compose --env-file .env ps
echo
echo "Web:  http://127.0.0.1:${WEB_HOST_PORT:-5173}"
echo "API:  http://127.0.0.1:${API_HOST_PORT:-8000}/docs"
echo "Health: curl -s http://127.0.0.1:${API_HOST_PORT:-8000}/health"
echo "Postgres host: localhost:${POSTGRES_PORT:-5433}  Redis host: localhost:${REDIS_PORT:-6380}"
