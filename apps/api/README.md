# Mo API (`apps/api`)

Q1/Q2 FastAPI shell aligned with `docs/drafts/openapi-v1.yaml` (`1.0.0-draft`).

- Contract base: **`/api/v1`** (OpenAPI `servers.url`)
- Health: **`GET /api/v1/health`** (preferred); root **`GET /health`** is a probe alias
- Auth stubs: `/api/v1/auth/login|logout|me`
- Projects CRUD (PUT primary; PATCH compat), mems / history / materials / jobs stubs
- Default `memsSchemaVersion`: **`1.0.0-draft`**

## Requirements

- Python 3.11+
- Optional deps: Postgres on host **5433**, Redis on host **6380** (`make up` at repo root)

## Setup

```bash
cd /workspace/mo-platform/apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Host-side env (API process not inside compose network):

```bash
export DATABASE_URL=postgresql+psycopg://mo:mo@127.0.0.1:5433/mo
export REDIS_URL=redis://127.0.0.1:6380/0
```

If Postgres is down, the API still starts and keeps projects in memory; `/api/v1/health` reports `db.ok=false` with a clear error without failing the main `status=ok` path.

## Run

```bash
cd /workspace/mo-platform/apps/api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

OpenAPI: http://127.0.0.1:8000/docs  ·  http://127.0.0.1:8000/openapi.json

## Smoke curls

Base URL: `http://127.0.0.1:8000/api/v1` (contract). Probe alias: `GET /health` → same payload as `GET /api/v1/health`.

```bash
BASE=http://127.0.0.1:8000/api/v1

# Health (contract path + root alias)
curl -s "$BASE/health"
curl -s http://127.0.0.1:8000/health

# Auth
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/auth/me"

# 401 without token
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/projects"

# Projects
curl -s -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo-rf-pmsm","topology":"RF","machineType":"PMSM"}' \
  "$BASE/projects"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/projects?limit=20&offset=0"
```

### Mems round-trip (Q1 shell)

```bash
BASE=http://127.0.0.1:8000/api/v1
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')

# 1) create project
PID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"mems-smoke","topology":"RF","machineType":"PMSM"}' \
  "$BASE/projects" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

# 2) GET mems (builds + persists minimal zip; checksum stable on repeat)
curl -s -H "Authorization: Bearer $TOKEN" -o /tmp/p.mems "$BASE/projects/$PID/mems"
sha256sum /tmp/p.mems
curl -s -H "Authorization: Bearer $TOKEN" -o /tmp/p2.mems "$BASE/projects/$PID/mems"
sha256sum /tmp/p2.mems   # same as p.mems

# 3) PUT multipart replace (field name: file)
curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/p.mems;type=application/zip" \
  "$BASE/projects/$PID/mems"

# 3b) POST import (same validation as PUT)
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/p.mems;type=application/zip" \
  "$BASE/projects/$PID/mems/import"

# 3c) Import repo sample (Q1-2 minimal RF+PMSM; dual-track versions + rotor.poleCount)
#     docs/samples/minimal-rf-pmsm.mems — memsSchemaVersion=1.0.0-draft,
#     geometry/params.json schemaVersion=0.1.0-q1, rotor.poleCount (positive even)
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@../../docs/samples/minimal-rf-pmsm.mems;type=application/zip" \
  "$BASE/projects/$PID/mems/import"

# 4) export alias (same bytes as GET /mems)
curl -s -H "Authorization: Bearer $TOKEN" -o /tmp/p-export.mems \
  "$BASE/projects/$PID/mems/export"
sha256sum /tmp/p.mems /tmp/p-export.mems

# Negative: non-zip → 400 bad_request
echo 'not-a-zip' >/tmp/bad.mems
curl -s -o /dev/null -w '%{http_code}\n' -X PUT -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/zip' --data-binary @/tmp/bad.mems \
  "$BASE/projects/$PID/mems"
```

Also: history empty stub —

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/projects/$PID/history"
```

### Sync analytic solve (path + Docker)

`POST /api/v1/solver/analytic/solve` loads `packages/solver-analytic` via:

1. Env **`SOLVER_ANALYTIC_PATH`** (or `MO_SOLVER_ANALYTIC_PATH`) — directory containing `solve.py`
2. Else walk parents for `packages/solver-analytic/solve.py` (host monorepo)
3. Else `apps/api/vendor/solver-analytic` (optional vendored copy)

Compose builds the API from **repo root** so the image includes the package at
`/opt/mo/packages/solver-analytic` and sets `SOLVER_ANALYTIC_PATH` accordingly.
After pulling solver or Dockerfile changes: `docker compose build api && docker compose up -d api`
(or `make up` from repo root). Mo-运维 owns compose; this context/`ENV` change is required for sync solve in containers.

### Materials (Q2-1 typed curves)

Aligned to architecture tip `3c34f1c` / OpenAPI `Material`: required `id`, `name`, `category`, `builtin`, `materialsSchemaVersion` (`0.1.0-q2`); typed `curves` by category (`curves.steel|magnet|coil|acim_bar`); `meta` is extension bag only (old camelCase keys kept for transition). Builtin seeds are read-only (PUT/DELETE → 403). Soft-delete via DELETE sets `deletedAt`.

```bash
# List all / filter
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/materials" | python3 -m json.tool | head
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/materials?category=steel"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/materials?category=acim_bar"

# Get one (stable ids) — prefer curves.* over meta
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/materials/mat-steel-m19"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/materials/mat-ndfeb-n42"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/materials/mat-acim-bar-al"

# Create custom (builtin forced false; curves required)
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"My Steel","category":"steel","curves":{"steel":{"bh":{"xName":"H","yName":"B","xUnit":"A/m","yUnit":"T","points":[[0,0],[200,1.0],[8000,1.8]]}}}}' \
  "$BASE/materials"

# Builtin write rejection (expect 403)
curl -s -o /dev/null -w '%{http_code}\n' -X PUT -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"x","category":"steel","curves":{"steel":{"bh":{"xName":"H","yName":"B","points":[[0,0],[1,1]]}}}}' \
  "$BASE/materials/mat-steel-m19"
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE -H "Authorization: Bearer $TOKEN" \
  "$BASE/materials/mat-steel-m19"

# Sync analytic solve (Python golden; Bearer required). Query solver=mec|mock
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d @../../packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json \
  "$BASE/solver/analytic/solve?solver=mec" | python3 -m json.tool | head -40

curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d @../../packages/solver-analytic/smoke/fixtures/radial_acim_request.json \
  "$BASE/solver/analytic/solve" | python3 -m json.tool | head -40

# mock path
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d @../../packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json \
  "$BASE/solver/analytic/solve?solver=mock" | python3 -m json.tool | head -20
```

### Jobs analytic poll (Q2-6 optional Celery)

`jobType=analytic`: set `CELERY_ENABLED=1` **and** run a worker with reachable Redis (`REDIS_URL`) to enqueue (`queued`→`running`→`succeeded`). Otherwise the API **degrades** to an in-process daemon thread with the same status transitions (default; API shape unchanged). Redis down / enqueue error also degrades. `fem` / `optimize` stay `queued` placeholders (Q3/Q4).

```bash
# Need a project id — reuse $PID from mems smoke or create one
JOB=$(curl -s -X POST -H "Authorization: Bearer $TOKEN"   -H 'Content-Type: application/json'   -d "{"projectId":"$PID","jobType":"analytic","payload":{"mode":"smoke"}}"   "$BASE/jobs")
echo "$JOB" | python3 -m json.tool
JID=$(echo "$JOB" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

# Poll until succeeded (degrade path typically <200ms)
for i in 1 2 3 4 5 6 7 8 9 10; do
  ST=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE/jobs/$JID")
  echo "$ST" | python3 -c 'import sys,json; j=json.load(sys.stdin); print(j["status"], j.get("resultRef"))'
  echo "$ST" | python3 -c 'import sys,json; raise SystemExit(0 if json.load(sys.stdin)["status"] in ("succeeded","failed") else 1)' && break
  sleep 0.2
done
```

### Celery worker (optional)

Host (Redis on published **6380**):

```bash
cd /workspace/mo-platform/apps/api
source .venv/bin/activate
export REDIS_URL=redis://127.0.0.1:6380/0
export CELERY_ENABLED=1   # also set on the API process
celery -A app.celery_app worker --loglevel=INFO
```

Compose: see commented `worker` stub in repo `docker-compose.yml` (ops owns compose; uncomment when needed). Default API (`CELERY_ENABLED` unset/false) always uses in-process degrade so poll-to-succeeded works without a worker.
