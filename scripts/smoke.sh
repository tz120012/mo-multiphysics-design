#!/usr/bin/env bash
# Static checks (no Docker required). Default path unchanged.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[mo-platform] smoke: checking required files"
test -f docker-compose.yml
test -f docker-compose.box.yml
test -f .github/workflows/ci.yml
test -f apps/api/Dockerfile
test -f apps/web/Dockerfile
test -f apps/web/nginx.box.conf
test -f docs/deploy-local.md

echo "[mo-platform] smoke: compose defines postgres/redis/api/web"
grep -qE '^[[:space:]]*postgres:' docker-compose.yml
grep -qE '^[[:space:]]*redis:' docker-compose.yml
grep -qE '^[[:space:]]*api:' docker-compose.yml
grep -qE '^[[:space:]]*web:' docker-compose.yml

echo "[mo-platform] smoke: host ports default 5433/6380"
grep -q '5433' docker-compose.yml
grep -q '6380' docker-compose.yml

echo "[mo-platform] smoke: box overlay uses host.docker.internal"
grep -q 'host.docker.internal' docker-compose.box.yml

echo "[mo-platform] Gate0/Q1 smoke placeholder: ok"
exit 0
