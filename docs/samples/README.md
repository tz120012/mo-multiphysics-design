# `.mems` samples (Q1-2)

| 文件 | 说明 |
| --- | --- |
| [`minimal-rf-pmsm.mems`](./minimal-rf-pmsm.mems) | 最小 RF+PMSM 样例包：`memsSchemaVersion=1.0.0`；`geometry/params.json` `schemaVersion=0.1.0-q1`；权威极数 `rotor.poleCount`（正偶数，电气极对数=`poleCount/2` 派生） |

## Import 冒烟

API 基址 `/api/v1`（探针别名 `GET /health`）：

```bash
BASE=http://127.0.0.1:8000/api/v1
TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json'   -d '{"username":"demo","password":"demo"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')
PID=$(curl -s -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json'   -d '{"name":"import-sample","topology":"RF","machineType":"PMSM"}'   "$BASE/projects" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
curl -s -X POST -H "Authorization: Bearer $TOKEN"   -F "file=@docs/samples/minimal-rf-pmsm.mems;type=application/zip"   "$BASE/projects/$PID/mems/import"
```
