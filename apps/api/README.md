# Mo API (`apps/api`)

Q1 FastAPI shell aligned with `docs/drafts/openapi-v1.yaml` (`1.0.0-draft`).

- Contract base: `/api/v1` (OpenAPI `servers.url`)
- Health: **`GET /api/v1/health`** (preferred); root `GET /health` is a probe alias
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

```bash
# Health (contract path + root alias)
curl -s http://127.0.0.1:8000/api/v1/health
curl -s http://127.0.0.1:8000/health

# Auth
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/v1/auth/me

# 401 without token
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/api/v1/projects

# Projects
curl -s -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo-rf-pmsm","topology":"RF","machineType":"PMSM"}' \
  http://127.0.0.1:8000/api/v1/projects
curl -s -H "Authorization: Bearer $TOKEN" 'http://127.0.0.1:8000/api/v1/projects?limit=20&offset=0'

# Mems / history / materials (replace PROJECT_ID)
# curl -s -H "Authorization: Bearer $TOKEN" -o /tmp/p.mems http://127.0.0.1:8000/api/v1/projects/$PID/mems
# curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/v1/projects/$PID/history
# curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/v1/materials
```
