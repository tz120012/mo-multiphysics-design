#!/usr/bin/env bash
# Q4-10 Jobs analytic/fem dry-run enqueue + poll — Mo-运维.
# Requires running API (and preferably worker + worker-fem). Keeps MO_FEM_DRY_RUN=1.
# Does not flip dry-run; does not claim FEM ≤3%/≤5%.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
JOBS_N="${JOBS_N:-8}"
POLL_SEC="${POLL_SEC:-60}"
DEMO_USER="${DEMO_USER:-demo}"
DEMO_PASS="${DEMO_PASS:-demo}"

API="${BASE_URL%/}/api/v1"

echo "=== mo-platform stress-jobs (Q4-10 Jobs extension) ==="
echo "ROOT=$ROOT"
echo "BASE_URL=$BASE_URL  JOBS_N=$JOBS_N  POLL_SEC=$POLL_SEC"
echo "MO_FEM_DRY_RUN must stay 1 (this script never flips it)"
echo

if ! curl -sf -o /dev/null --max-time 5 "${BASE_URL}/health"; then
  echo "FAIL: health never ok (GET ${BASE_URL}/health)"
  echo "summary: analytic_ok=0 analytic_fail=0 fem_ok=0 fem_fail=0 RESULT=FAIL"
  exit 1
fi
echo "initial health: ok"

LOGIN_RESP="$(curl -sS -w '\n%{http_code}' --max-time 10 \
  -X POST "${API}/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"${DEMO_USER}\",\"password\":\"${DEMO_PASS}\"}")"
LOGIN_BODY="$(printf '%s' "$LOGIN_RESP" | sed '$d')"
LOGIN_CODE="$(printf '%s' "$LOGIN_RESP" | tail -n1)"
if [[ "$LOGIN_CODE" != "200" ]]; then
  echo "FAIL: login HTTP $LOGIN_CODE"
  echo "$LOGIN_BODY"
  exit 1
fi
TOKEN="$(printf '%s' "$LOGIN_BODY" | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')"
echo "login: ok (demo)"

PROJ_NAME="stress-jobs-$(date +%Y%m%d-%H%M%S)-$$"
PROJ_RESP="$(curl -sS -w '\n%{http_code}' --max-time 10 \
  -X POST "${API}/projects" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"${PROJ_NAME}\",\"topology\":\"RF\",\"machineType\":\"PMSM\"}")"
PROJ_BODY="$(printf '%s' "$PROJ_RESP" | sed '$d')"
PROJ_CODE="$(printf '%s' "$PROJ_RESP" | tail -n1)"
if [[ "$PROJ_CODE" != "201" && "$PROJ_CODE" != "200" ]]; then
  echo "FAIL: create project HTTP $PROJ_CODE"
  echo "$PROJ_BODY"
  exit 1
fi
PID="$(printf '%s' "$PROJ_BODY" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')"
echo "projectId: $PID"

TMPDIR_STRESS="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_STRESS"' EXIT
JOBS_FILE="$TMPDIR_STRESS/jobs.tsv"
: >"$JOBS_FILE"

enqueue_one() {
  local kind="$1"
  local payload
  if [[ "$kind" == "analytic" ]]; then
    payload="$(python3 -c "import json; print(json.dumps({
      'projectId': '${PID}',
      'jobType': 'analytic',
      'payload': {'mode': 'smoke'},
    }))")"
  else
    payload="$(python3 -c "import json; print(json.dumps({
      'projectId': '${PID}',
      'jobType': 'fem',
      'payload': {
        'topology': 'RF',
        'machineType': 'PMSM',
        'dim': '2d',
        'solverKernel': 'elmer',
        'meshProfile': 'coarse',
        'operatingPoint': {'rpm': 3000},
        'materials': {'magnet': 'N42'},
        'templateId': 'rf_pmsm_2d',
      },
    }))")"
  fi
  local resp code body jid
  resp="$(curl -sS -w '\n%{http_code}' --max-time 15 \
    -X POST "${API}/jobs" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "$payload")"
  body="$(printf '%s' "$resp" | sed '$d')"
  code="$(printf '%s' "$resp" | tail -n1)"
  if [[ "$code" != "202" ]]; then
    echo "FAIL: enqueue ${kind} HTTP $code"
    echo "$body"
    echo "${kind}	ENQUEUE_FAIL	${code}" >>"$JOBS_FILE"
    return 0
  fi
  jid="$(printf '%s' "$body" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')"
  echo "enqueued ${kind}: $jid (202)"
  echo "${kind}	${jid}	queued" >>"$JOBS_FILE"
}

echo
echo "--- enqueue (${JOBS_N} analytic + ${JOBS_N} fem) ---"
START_EPOCH="$(date +%s)"
for ((i = 1; i <= JOBS_N; i++)); do
  enqueue_one analytic
  enqueue_one fem
done

echo
echo "--- poll (timeout ${POLL_SEC}s) ---"
deadline=$((START_EPOCH + POLL_SEC))
while true; do
  pending=0
  while IFS=$'\t' read -r kind jid status; do
    [[ "$status" == "succeeded" || "$status" == "failed" || "$status" == "ENQUEUE_FAIL" || "$status" == "timeout" ]] && continue
    [[ "$jid" == "ENQUEUE_FAIL" ]] && continue
    st_json="$(curl -sS --max-time 10 \
      -H "Authorization: Bearer ${TOKEN}" \
      "${API}/jobs/${jid}" || true)"
    new_status="$(printf '%s' "$st_json" | python3 -c 'import sys,json
try:
  print(json.load(sys.stdin).get("status", "unknown"))
except Exception:
  print("unknown")' 2>/dev/null || echo unknown)"
    if [[ "$new_status" == "succeeded" || "$new_status" == "failed" ]]; then
      # rewrite line
      tmpf="$TMPDIR_STRESS/jobs.new"
      : >"$tmpf"
      while IFS=$'\t' read -r k j s; do
        if [[ "$j" == "$jid" ]]; then
          echo -e "${k}\t${j}\t${new_status}" >>"$tmpf"
        else
          echo -e "${k}\t${j}\t${s}" >>"$tmpf"
        fi
      done <"$JOBS_FILE"
      mv "$tmpf" "$JOBS_FILE"
      echo "  ${kind} ${jid} -> ${new_status}"
    else
      pending=$((pending + 1))
    fi
  done <"$JOBS_FILE"

  if ((pending == 0)); then
    break
  fi
  now="$(date +%s)"
  if ((now >= deadline)); then
    echo "WARN: poll timeout after ${POLL_SEC}s (${pending} still pending)"
    tmpf="$TMPDIR_STRESS/jobs.new"
    : >"$tmpf"
    while IFS=$'\t' read -r k j s; do
      if [[ "$s" != "succeeded" && "$s" != "failed" && "$s" != "ENQUEUE_FAIL" && "$s" != "timeout" ]]; then
        echo -e "${k}\t${j}\ttimeout" >>"$tmpf"
      else
        echo -e "${k}\t${j}\t${s}" >>"$tmpf"
      fi
    done <"$JOBS_FILE"
    mv "$tmpf" "$JOBS_FILE"
    break
  fi
  sleep 1
done

END_EPOCH="$(date +%s)"
WALL=$((END_EPOCH - START_EPOCH))

analytic_ok=0
analytic_fail=0
fem_ok=0
fem_fail=0
while IFS=$'\t' read -r kind jid status; do
  if [[ "$kind" == "analytic" ]]; then
    if [[ "$status" == "succeeded" ]]; then
      analytic_ok=$((analytic_ok + 1))
    else
      analytic_fail=$((analytic_fail + 1))
    fi
  elif [[ "$kind" == "fem" ]]; then
    if [[ "$status" == "succeeded" ]]; then
      fem_ok=$((fem_ok + 1))
    else
      fem_fail=$((fem_fail + 1))
    fi
  fi
done <"$JOBS_FILE"

# Optional: peek one succeeded fem job for dryRun in result/artifacts if present
DRYRUN_NOTE="n/a"
first_fem_ok="$(awk -F'\t' '$1=="fem" && $3=="succeeded"{print $2; exit}' "$JOBS_FILE" || true)"
if [[ -n "${first_fem_ok:-}" ]]; then
  art="$(curl -sS --max-time 10 \
    -H "Authorization: Bearer ${TOKEN}" \
    "${API}/jobs/${first_fem_ok}/artifacts/solver/fem/jobs/${first_fem_ok}/manifest.json" 2>/dev/null || true)"
  if [[ -n "$art" ]]; then
    DRYRUN_NOTE="$(printf '%s' "$art" | python3 -c 'import sys,json
try:
  m=json.load(sys.stdin)
  s=m.get("scalars") or {}
  print("dryRun="+str(s.get("dryRun", m.get("dryRun", "?"))).lower())
except Exception as e:
  print("parse_err")' 2>/dev/null || echo parse_err)"
  else
    # fallback: job GET may embed result
    stj="$(curl -sS --max-time 10 -H "Authorization: Bearer ${TOKEN}" "${API}/jobs/${first_fem_ok}" || true)"
    DRYRUN_NOTE="$(printf '%s' "$stj" | python3 -c 'import sys,json
try:
  j=json.load(sys.stdin)
  print("resultRef="+str(j.get("resultRef") or "none"))
except Exception:
  print("n/a")' 2>/dev/null || echo n/a)"
  fi
fi

RESULT="PASS"
if ((analytic_fail > 0 || fem_fail > 0)); then
  RESULT="FAIL"
fi

echo
echo "=== summary (paste into Q4-10 report) ==="
echo "endpoint: POST ${API}/jobs (analytic + fem dry-run)"
echo "JOBS_N: ${JOBS_N} (each type)"
echo "POLL_SEC: ${POLL_SEC}"
echo "projectId: ${PID}"
echo "analytic_ok: ${analytic_ok}"
echo "analytic_fail: ${analytic_fail}"
echo "fem_ok: ${fem_ok}"
echo "fem_fail: ${fem_fail}"
echo "wall_sec: ${WALL}"
echo "fem_manifest_sample: ${DRYRUN_NOTE}"
echo "threshold: exit non-zero if any fail or timeout"
echo "RESULT: ${RESULT}"

if [[ "$RESULT" != "PASS" ]]; then
  exit 1
fi
exit 0
