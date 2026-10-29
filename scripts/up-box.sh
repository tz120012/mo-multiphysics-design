#!/usr/bin/env bash
# Box 四服务：必须双文件（docker-compose.yml + docker-compose.box.yml）。
# 禁止裸 docker compose up —— 会漂回服务 DNS / 镜像内 nginx，:5174 代理挂死。
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || cp .env.example .env

DC="docker compose"
if ! docker compose version >/dev/null 2>&1; then
  DC="sudo docker compose"
elif ! docker info >/dev/null 2>&1; then
  DC="sudo docker compose"
fi

echo "[mo] up-box: -f docker-compose.yml -f docker-compose.box.yml"
echo "[mo] 禁止随后再跑裸 docker compose up / scripts/start-deps.sh（会覆盖 overlay）"
$DC -f docker-compose.yml -f docker-compose.box.yml --env-file .env up -d --build
curl -sf "http://127.0.0.1:${API_HOST_PORT:-8000}/health" | python3 -m json.tool || true
bash scripts/assert-box-overlay.sh || true
