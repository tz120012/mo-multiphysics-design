#!/usr/bin/env bash
# Box + worker + fem：双文件 overlay。worker / worker-fem 也必须带 box
#（DATABASE_URL/REDIS_URL → host.docker.internal:5433/6380），否则 Celery 连不上 broker。
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || cp .env.example .env

DC="docker compose"
if ! docker compose version >/dev/null 2>&1; then
  DC="sudo docker compose"
elif ! docker info >/dev/null 2>&1; then
  DC="sudo docker compose"
fi

echo "[mo] up-fem-box: box overlay + profiles worker,fem（默认 MO_FEM_DRY_RUN=1）"
echo "[mo] 禁止随后再跑裸 docker compose --profile worker|fem up（worker 会漂回 postgres/redis DNS）"
CELERY_ENABLED=1 $DC -f docker-compose.yml -f docker-compose.box.yml \
  --env-file .env --profile worker --profile fem up -d --build
curl -sf "http://127.0.0.1:${API_HOST_PORT:-8000}/health" | python3 -m json.tool || true
bash scripts/assert-box-overlay.sh || true
