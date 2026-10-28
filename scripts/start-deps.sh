#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || cp .env.example .env
docker compose --env-file .env up -d
docker compose --env-file .env ps
echo "Postgres host: localhost:${POSTGRES_PORT:-5433}  Redis host: localhost:${REDIS_PORT:-6380}"
