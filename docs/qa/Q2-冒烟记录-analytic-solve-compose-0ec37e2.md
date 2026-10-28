# Q2 冒烟记录 — compose 路径 analytic solve tip `0ec37e2`

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:34 Asia/Shanghai |
| 指派 tip | **`0ec37e2`**（`fix(api): robust solver-analytic path + package into api image`） |
| 祖先确认 | `git merge-base --is-ancestor 0ec37e2 HEAD` → **0（是祖先）**；写证据时 **HEAD=`0ec37e2`** |
| 执行 | Mo-测试执行员 |
| 性质 | Motor：compose 路径复测；**禁止本机 uvicorn 顶替**；硬口径金标非 501 |

## 环境（证明 `:8000` = 容器镜像，非本机 uvicorn）

| 证据 | 结果 |
| --- | --- |
| 重建命令 | `sudo docker compose -f docker-compose.yml -f docker-compose.box.yml --env-file .env up -d --build --force-recreate api`（box 惯例 / `up-box` 同源 overlay） |
| `docker compose ps` | `mo-api` **Up (healthy)**；`0.0.0.0:8000->8000/tcp` |
| 本机 uvicorn | `pgrep -af 'apps/api\|.venv.*uvicorn'` → **无** |
| 容器内包 | `docker exec mo-api ls /opt/mo/packages/solver-analytic` → 含 `solve.py` / `radial_mec` / `api`；`SOLVER_ANALYTIC_PATH=/opt/mo/packages/solver-analytic` |
| 容器内 loopback | `docker exec` → `POST …/solver/analytic/solve?solver=mec` → **200**；`meta.mock=false`；`torque_nm=4.085849009960654` |
| Health | `GET /health` → `status=ok`，db/redis `ok=true`（宿主机映射口与容器内 loopback 一致） |

> 对照先前 `8b71df1` 记录：彼时 Dockerfile 未打 packages + `parents[4]` IndexError，compose 起不来，只能本机 uvicorn。本 tip 修复后 **compose 路径可关**。

## 金标依据

同 [Q2-冒烟记录-analytic-solve-8b71df1](Q2-冒烟记录-analytic-solve-8b71df1.md)：

- schema：`packages/solver-analytic/api/solve.schema.json` → `schema_version` / `meta` / `torque_nm` / `back_emf_v_peak` / `losses_w`
- fixture：`radial_pmsm_request.json` / `radial_acim_request.json`
- CLI：`python3 packages/solver-analytic/solve.py --solver=mec <fixture>`

## Motor 硬口径

| # | 硬口径 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | tip `0ec37e2` 是 HEAD 祖先（或拉到含 tip 的 HEAD） | HEAD=`0ec37e2`；`merge-base --is-ancestor` 通过 | **PASS** |
| 2 | compose 重建 api；`:8000` 来自容器 | 见上表；无本机 `.venv` uvicorn；容器内含 solver-analytic | **PASS** |
| 3 | 无鉴权 POST → 401/403 | `POST /api/v1/solver/analytic/solve` 无 Authorization → **401** `unauthorized` | **PASS** |
| 4 | 有鉴权 + PMSM mec → **200** 金标、**非 501** | Bearer + `?solver=mec` + PMSM fixture → **200**；`mock=false`；字段齐全；数值与 CLI 金标一致 | **PASS** |
| 5 | ACIM 抽测 → 200 | ACIM fixture + auth → **200**；`meta.solver=acim_equiv`；`mock=false`；含 `losses_w.rotor_bar` | **PASS** |

### 命令摘要

```bash
cd /workspace/mo-platform
git merge-base --is-ancestor 0ec37e2 HEAD; echo $?   # → 0
sudo docker compose -f docker-compose.yml -f docker-compose.box.yml --env-file .env up -d --build --force-recreate api
sudo docker compose -f docker-compose.yml -f docker-compose.box.yml --env-file .env ps
# 无本机 uvicorn
pgrep -af 'apps/api|.venv.*uvicorn' || echo 'no host venv uvicorn'

BASE=http://127.0.0.1:8000/api/v1
# 无鉴权 → 401
curl -s -w '\nHTTP %{http_code}\n' -X POST "$BASE/solver/analytic/solve" \
  -H 'Content-Type: application/json' \
  -d @packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json

TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')

# PMSM mec → 200 金标
curl -s -w '\nHTTP %{http_code}\n' -X POST "$BASE/solver/analytic/solve?solver=mec" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d @packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json

# ACIM → 200
curl -s -w '\nHTTP %{http_code}\n' -X POST "$BASE/solver/analytic/solve" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d @packages/solver-analytic/smoke/fixtures/radial_acim_request.json
```

### 有鉴权 PMSM（compose）关键字段

```json
{
  "schema_version": "0.0.0-gate0",
  "meta": { "solver": "mec", "elapsed_ms": 0.773, "mock": false },
  "torque_nm": 4.085849009960654,
  "back_emf_v_peak": 34.229528622318725,
  "losses_w": {
    "copper": 59.99790718364898,
    "iron": 35.31789439296892,
    "magnet_eddy": 0.016491355833849045
  },
  "inductance_h": {
    "ld": 0.00010458551861539656,
    "lq": 0.00010725679244472132
  }
}
```

与 CLI 金标（同 fixture `--solver=mec`）`torque_nm` / `back_emf_v_peak` / `losses_w` **数值一致**。

### ACIM 抽测（compose）摘要

- HTTP **200**；`meta.solver=acim_equiv`；`meta.mock=false`
- `torque_nm=145.8441451429567`；`losses_w.rotor_bar` 存在

## 未动项

- **未**改业务代码 / Dockerfile / compose。
- **未**用本机 uvicorn 冒充 PASS。
- **未**改 Q2-P01 / P02 / P03 / P04 / P06 主状态；仅在跟踪表补 compose 路径 PASS 备注（主状态以产品表为准）。
- Wasm UI 闭环不在本任务范围（另 tip / 证据）。

## 结论

| 项 | 结论 |
| --- | --- |
| tip `0ec37e2` 祖先 / HEAD | **确认** |
| compose 重建 api + 容器 `:8000` | **PASS** |
| 无鉴权 401 | **PASS** |
| 有鉴权 PMSM mec 200 金标非 501（`mock=false`） | **PASS** |
| ACIM 抽测 200（`mock=false`） | **PASS** |
| **总判** | **PASS** |
