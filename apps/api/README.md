# Mo API (`apps/api`)

Q1-1 FastAPI shell: `/health`, Bearer auth placeholder, projects CRUD, OpenAPI.

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

If Postgres is down, the API still starts and keeps projects in memory; `/health` reports `db.ok=false` with a clear error without failing the main `status=ok` path.

## Run

```bash
cd /workspace/mo-platform/apps/api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

OpenAPI: http://127.0.0.1:8000/docs  ·  http://127.0.0.1:8000/openapi.json

## Smoke curls

```bash
curl -s http://127.0.0.1:8000/health
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/api/v1/projects
curl -s -H 'Authorization: Bearer demo' \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo-rf-pmsm","topology":"RF","machineType":"PMSM"}' \
  http://127.0.0.1:8000/api/v1/projects
curl -s -H 'Authorization: Bearer demo' http://127.0.0.1:8000/api/v1/projects
```
