#!/usr/bin/env bash
# Assert running mo-api / mo-web / mo-worker / mo-worker-fem still carry box overlay.
# Exit 0 = all present containers look box-aligned; non-zero = drift.
set -euo pipefail

DK=docker
if ! docker info >/dev/null 2>&1; then
  DK="sudo docker"
fi

fail=0
running() {
  $DK ps --format '{{.Names}}' 2>/dev/null | grep -qx "$1"
}

check_one() {
  local cname="$1" need_nginx="${2:-0}"
  if ! running "$cname"; then
    echo "[skip] ${cname} not running"
    return 0
  fi
  local files hosts db nginx_hit
  files=$($DK inspect "$cname" --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}' 2>/dev/null || true)
  hosts=$($DK inspect "$cname" --format '{{json .HostConfig.ExtraHosts}}' 2>/dev/null || true)
  echo "== ${cname} =="
  echo "  config_files: ${files:-?}"
  echo "  ExtraHosts:   ${hosts:-?}"
  if [[ "$files" != *docker-compose.box.yml* ]]; then
    echo "  FAIL: config_files missing docker-compose.box.yml（裸 compose 覆盖了 overlay）"
    fail=1
  fi
  if [[ "$hosts" != *host.docker.internal* ]]; then
    echo "  FAIL: ExtraHosts missing host.docker.internal:host-gateway"
    fail=1
  fi
  case "$cname" in
    mo-api|mo-worker|mo-worker-fem)
      db=$($DK exec "$cname" printenv DATABASE_URL 2>/dev/null || true)
      echo "  DATABASE_URL: ${db:-?}"
      if [[ "$db" != *host.docker.internal* ]]; then
        echo "  FAIL: DATABASE_URL 仍指向服务名 postgres（应 host.docker.internal:5433）"
        fail=1
      fi
      ;;
  esac
  if [[ "$need_nginx" == "1" ]]; then
    # 仅有效配置行（去掉 # 注释），避免 nginx.box.conf 说明文字误报
    nginx_active=$($DK exec "$cname" sh -c "grep -vE '^[[:space:]]*#' /etc/nginx/conf.d/default.conf | grep -E 'proxy_pass|resolver'" 2>/dev/null || true)
    echo "  nginx proxy (active):"
    printf '%s\n' "$nginx_active" | sed 's/^/    /'
    if ! printf '%s\n' "$nginx_active" | grep -q 'host.docker.internal'; then
      echo "  FAIL: nginx 非 nginx.box.conf（缺 host.docker.internal 字面量 proxy_pass）"
      fail=1
    fi
    if printf '%s\n' "$nginx_active" | grep -qE 'resolver[[:space:]]+127\.0\.0\.11'; then
      echo "  FAIL: nginx 仍含 resolver 127.0.0.11（会超时）"
      fail=1
    fi
  fi
}

check_one mo-api
check_one mo-web 1
check_one mo-worker
check_one mo-worker-fem

if [[ "$fail" -ne 0 ]]; then
  echo
  echo "[mo] box overlay 已漂。修复（保留 FEM 时）："
  echo "  CELERY_ENABLED=1 sudo docker compose -f docker-compose.yml -f docker-compose.box.yml \\"
  echo "    --env-file .env --profile worker --profile fem \\"
  echo "    up -d --force-recreate --no-deps api web worker worker-fem"
  echo "或：make up-fem-box / ./scripts/up-fem-box.sh"
  echo "禁止：裸 docker compose up / scripts/start-deps.sh（会丢掉 overlay）"
  exit 1
fi
echo
echo "[mo] box overlay OK（已运行服务均含 docker-compose.box.yml + host.docker.internal）"
exit 0
