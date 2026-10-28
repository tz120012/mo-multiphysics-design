# Mo API (`apps/api`)

Q1 FastAPI shell aligned with `docs/drafts/openapi-v1.yaml` (`1.0.0-draft`).

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

Also: history / materials stubs —

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/projects/$PID/history"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/materials"
```
