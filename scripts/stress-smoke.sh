#!/usr/bin/env bash
# Q4-10 stress entry skeleton — Mo-运维.
# Requires a running API (curl only); does not start Docker.
# Extension points (later): Jobs enqueue/poll, optional hey/ab if installed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
CONCURRENCY="${CONCURRENCY:-8}"
REQUESTS="${REQUESTS:-40}"
HEALTH_PATH="${HEALTH_PATH:-/health}"
# Optional auth (skeleton): set DEMO_USER / DEMO_PASS to attempt one login; unused paths skipped if unset.
DEMO_USER="${DEMO_USER:-}"
DEMO_PASS="${DEMO_PASS:-}"

TMPDIR_STRESS="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_STRESS"' EXIT

ok_file="$TMPDIR_STRESS/ok"
fail_file="$TMPDIR_STRESS/fail"
: >"$ok_file"
: >"$fail_file"

echo "=== mo-platform stress-smoke (Q4-10 skeleton) ==="
echo "ROOT=$ROOT"
echo "BASE_URL=$BASE_URL  CONCURRENCY=$CONCURRENCY  REQUESTS=$REQUESTS"
echo "target: GET ${BASE_URL}${HEALTH_PATH}"
echo

# Probe once before parallel load
if ! curl -sf -o /dev/null --max-time 5 "${BASE_URL}${HEALTH_PATH}"; then
  echo "FAIL: health never ok (initial GET ${BASE_URL}${HEALTH_PATH})"
  echo "summary: ok=0 fail=0 total=0 failure_rate=n/a initial_health=fail"
  exit 1
fi
echo "initial health: ok"

# Optional: one light authenticated GET if credentials provided (keep skeleton simple)
if [[ -n "$DEMO_USER" && -n "$DEMO_PASS" ]]; then
  echo "DEMO credentials set — extension point: login + light GET (not required for pass/fail)"
  # Placeholder: document for Q4-10 report; do not fail skeleton on auth errors
  curl -sf -o /dev/null --max-time 5 -u "${DEMO_USER}:${DEMO_PASS}" \
    "${BASE_URL}${HEALTH_PATH}" 2>/dev/null \
    && echo "optional auth probe: ok" \
    || echo "optional auth probe: skipped/fail (ignored)"
fi

one_request() {
  local i="$1"
  if curl -sf -o /dev/null --max-time 10 "${BASE_URL}${HEALTH_PATH}"; then
    echo 1 >>"$ok_file"
  else
    echo 1 >>"$fail_file"
  fi
}

# Parallel batching with bash background jobs (no hey/ab required)
running=0
for ((i = 1; i <= REQUESTS; i++)); do
  one_request "$i" &
  running=$((running + 1))
  if ((running >= CONCURRENCY)); then
    wait -n 2>/dev/null || wait
    running=$((running - 1))
  fi
done
wait

ok_count=$(wc -l <"$ok_file" | tr -d ' ')
fail_count=$(wc -l <"$fail_file" | tr -d ' ')
total=$((ok_count + fail_count))
if ((total == 0)); then
  echo "FAIL: no requests completed"
  echo "summary: ok=0 fail=0 total=0 failure_rate=n/a"
  exit 1
fi

# failure rate as percent * 100 for integer math (e.g. 10% => 1000)
fail_bp=$((fail_count * 10000 / total))
fail_pct_int=$((fail_count * 100 / total))
fail_pct_rem=$(((fail_count * 10000 / total) % 100))

echo
echo "=== summary (paste into Q4-10 report) ==="
echo "endpoint: GET ${BASE_URL}${HEALTH_PATH}"
echo "concurrency: ${CONCURRENCY}"
echo "requests: ${REQUESTS}"
echo "ok: ${ok_count}"
echo "fail: ${fail_count}"
echo "total: ${total}"
printf "failure_rate: %d.%02d%%\n" "$fail_pct_int" "$fail_pct_rem"
echo "threshold: fail if failure_rate > 10% or initial health never ok"
echo "extension_points: Jobs enqueue (analytic/fem dry-run); optional hey/ab if present"
if command -v hey >/dev/null 2>&1; then
  echo "note: hey is available on PATH (not used by this skeleton)"
elif command -v ab >/dev/null 2>&1; then
  echo "note: ab is available on PATH (not used by this skeleton)"
fi

# > 10% => fail_bp > 1000
if ((fail_bp > 1000)); then
  echo "RESULT: FAIL (failure rate > 10%)"
  exit 1
fi

echo "RESULT: PASS"
exit 0
