#!/usr/bin/env bash
# Gate0 smoke — docs / skeleton / CI placeholder / compose Postgres+Redis
# Exit 0 only if all automated checks pass. No business-feature tests.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

pass=0
fail=0
failures=()

ok() { echo "PASS  $1"; pass=$((pass + 1)); }
ng() { echo "FAIL  $1 — $2"; fail=$((fail + 1)); failures+=("$1"); }

echo "=== Gate0 smoke @ $(git rev-parse --short HEAD 2>/dev/null || echo 'NO-GIT') ==="
echo "cwd: $ROOT"
echo

# G0-S1 docs
if [[ -f docs/01-任务书-v2.md && -f docs/02-阶段任务拆解与门禁.md ]]; then
  ok "G0-S1 docs 01/02"
else
  ng "G0-S1" "缺少 docs/01-任务书-v2.md 或 docs/02-阶段任务拆解与门禁.md"
fi

# G0-S2 skeleton
missing=()
for d in apps/web apps/api packages/solver-analytic scripts docs; do
  [[ -d "$d" ]] || missing+=("$d")
done
[[ -f README.md ]] || missing+=("README.md")
[[ -f .gitignore ]] || missing+=(".gitignore")
if [[ ${#missing[@]} -eq 0 ]]; then
  ok "G0-S2 skeleton dirs"
else
  ng "G0-S2" "缺失: ${missing[*]}"
fi

# G0-S3 git
if git rev-parse HEAD >/dev/null 2>&1; then
  ok "G0-S3 git commit ($(git rev-parse --short HEAD))"
else
  ng "G0-S3" "无有效 git HEAD"
fi

# G0-S4 CI placeholder
ci_found=0
shopt -s nullglob
_ci_files=(.github/workflows/*.yml .github/workflows/*.yaml)
if ((${#_ci_files[@]} > 0)); then
  ci_found=1
elif [[ -f .gitlab-ci.yml || -f Jenkinsfile || -f .circleci/config.yml ]]; then
  ci_found=1
else
  _wp=(.woodpecker/*.yml .woodpecker/*.yaml)
  if ((${#_wp[@]} > 0)); then
    ci_found=1
  fi
fi
shopt -u nullglob
if [[ $ci_found -eq 1 ]]; then
  ok "G0-S4 CI placeholder"
else
  ng "G0-S4" "未找到 CI 配置（期望 .github/workflows/*.yml 或等价）"
fi

# G0-S5 compose Postgres + Redis
compose_file=""
for f in docker-compose.yml compose.yml docker-compose.yaml compose.yaml; do
  if [[ -f "$f" ]]; then compose_file="$f"; break; fi
done
if [[ -z "$compose_file" ]]; then
  # also accept docker-compose.*.yml
  for f in docker-compose.*.yml docker-compose.*.yaml; do
    [[ -f "$f" ]] || continue
    compose_file="$f"
    break
  done
fi
if [[ -z "$compose_file" ]]; then
  ng "G0-S5" "未找到 docker-compose.yml / compose.yml"
else
  body=$(tr '[:upper:]' '[:lower:]' < "$compose_file")
  has_pg=0
  has_redis=0
  echo "$body" | grep -E '(^|[[:space:]])(postgres|postgresql)(:|[[:space:]]|$)' >/dev/null && has_pg=1 || true
  echo "$body" | grep -E '(^|[[:space:]])redis(:|[[:space:]]|$)' >/dev/null && has_redis=1 || true
  # also match service keys like "postgres:" at line start after indent
  echo "$body" | grep -E '^[[:space:]]*(postgres|postgresql):' >/dev/null && has_pg=1 || true
  echo "$body" | grep -E '^[[:space:]]*redis:' >/dev/null && has_redis=1 || true
  if [[ $has_pg -eq 1 && $has_redis -eq 1 ]]; then
    ok "G0-S5 compose Postgres+Redis ($compose_file)"
  else
    ng "G0-S5" "$compose_file 缺少 postgres/postgresql 或 redis 服务定义"
  fi
fi

# G0-S6 this script is executable / present
if [[ -f scripts/smoke_gate0.sh ]]; then
  ok "G0-S6 smoke script present"
else
  ng "G0-S6" "scripts/smoke_gate0.sh 不存在"
fi

echo
echo "=== summary: pass=$pass fail=$fail ==="
if [[ $fail -gt 0 ]]; then
  echo "FAILED: ${failures[*]}"
  echo "Gate0 冒烟未通过 — 禁止开启业务代码。"
  exit 1
fi
echo "Gate0 自动化冒烟全部通过（角色确认与 Motor 签字仍须人工项 G0-P1/P2）。"
exit 0
