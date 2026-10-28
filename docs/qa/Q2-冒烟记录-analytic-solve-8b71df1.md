# Q2 冒烟记录 — sync analytic solve tip `8b71df1`

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:30 Asia/Shanghai |
| 指派 tip | **`8b71df1`**（`feat(api): wire sync analytic solve to Python golden`） |
| 祖先确认 | `git merge-base --is-ancestor 8b71df1 HEAD` → **0（是祖先）** |
| 仓库 HEAD（写证据时） | `5b5741b`（含 tip；后续 harden `027884e` / `493b0fe` 等同路径） |
| 执行 | Mo-测试执行员 |
| 性质 | Motor：API 冒烟（P01 已关）；硬口径「有鉴权金标、非 501」 |

## 环境

- tip 祖先链：**PASS**。
- **compose 镜像重建**：`sudo docker compose -f docker-compose.yml -f docker-compose.box.yml up -d --build api` 后容器 **无法启动**。
  - 根因：`apps/api/Dockerfile` 仅 `COPY app ./app`，容器内 `__file__=/app/app/routers/solver.py` → `Path.parents[4]` **IndexError: 4**（启动即崩）。
  - 另：镜像内无 `packages/solver-analytic`，即便 path 修好也会缺 golden 包（需运维/后端改 Dockerfile 或挂载，**本轮未改业务代码**）。
- **实测进程**：停掉坏容器后，本机 `apps/api/.venv` uvicorn `127.0.0.1:8000`（`DATABASE_URL=…5433` / `REDIS_URL=…6380`），加载仓库 tip 路径代码 + `packages/solver-analytic`（与 P06 本机抽测同法）。
- Health：`GET /health` → `status=ok`，db/redis `ok=true`。
- Auth：`POST /api/v1/auth/login` `demo/demo` → Bearer。

## 金标依据

| 来源 | 说明 |
| --- | --- |
| schema | `packages/solver-analytic/api/solve.schema.json` → `SolveResult` 必填：`schema_version` / `meta` / `torque_nm` / `back_emf_v_peak` / `losses_w` |
| 样例输入 | `packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json`（及 ACIM fixture） |
| CLI 对照 | `python3 packages/solver-analytic/solve.py --solver=mec <fixture>` 输出作为数值金标 |
| 判定 | HTTP **非 501**；200 body 含上述金标字段；PMSM 关键数值与 CLI 金标一致（相对容差 1e-6） |

## Motor 硬口径

| # | 硬口径 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | tip `8b71df1` 在祖先链（或镜像含 tip） | `merge-base --is-ancestor` 通过；本机 API 加载 tip 后代码（非 501 stub） | **PASS**（compose 镜像路径见环境，**未**作为本条否决） |
| 2 | 无鉴权 → 401/403 一类 | `POST /api/v1/solver/analytic/solve` 无 Authorization → **401** `unauthorized` / Missing or invalid Authorization | **PASS** |
| 3 | 有鉴权 → **200** + 金标字段，**非 501** | Bearer + PMSM fixture + `?solver=mec` → **200**；`schema_version=0.0.0-gate0`；`meta.solver=mec` `mock=false`；`torque_nm`/`back_emf_v_peak`/`losses_w`/`inductance_h` 齐全；与 CLI 金标数值一致 | **PASS** |

### 命令摘要

```bash
cd /workspace/mo-platform
git merge-base --is-ancestor 8b71df1 HEAD; echo $?   # → 0
# compose 重建（启动失败，见上）
sudo docker compose -f docker-compose.yml -f docker-compose.box.yml --env-file .env up -d --build api

# 本机 API（实测）
cd apps/api && source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg://mo:mo@127.0.0.1:5433/mo REDIS_URL=redis://127.0.0.1:6380/0
uvicorn app.main:app --host 127.0.0.1 --port 8000

BASE=http://127.0.0.1:8000/api/v1
# 无鉴权
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$BASE/solver/analytic/solve" \
  -H 'Content-Type: application/json' \
  -d @packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json
# → 401

TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')
curl -s -w '\nHTTP %{http_code}\n' -X POST "$BASE/solver/analytic/solve?solver=mec" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d @packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json
# → 200 + 金标
```

### 有鉴权 PMSM 响应关键字段（摘录）

```json
{
  "schema_version": "0.0.0-gate0",
  "meta": { "solver": "mec", "elapsed_ms": 0.798, "mock": false },
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

### 附加抽测（非硬否决）

| 用例 | 实测 | 说明 |
| --- | --- | --- |
| ACIM fixture + auth | **200**；`meta.solver=acim_equiv`；含 `losses_w.rotor_bar` | 与 tip 同端；对照 ACIM CLI |
| Bearer `bad` | **200**（stub 鉴权：非空 Bearer 即过） | Q1 stub 行为；硬口径只要求「无鉴权失败」 |

## 未动项

- **未**改 Q2-P01 / Q2-P04 / Q2-P06 状态。
- **未**改 `apps/` 业务代码；仅 `docs/qa`。

## 结论

| 项 | 结论 |
| --- | --- |
| 硬口径（无鉴权 401 / 有鉴权 200+金标非 501） | **PASS** |
| tip `8b71df1` 祖先 | **确认** |
| compose `:8000` 默认镜像 | **阻塞**（IndexError / 未打入 packages）；本轮以本机 uvicorn 完成冒烟 |
| 跟踪表建议 | P02/P03：**通过（API sync）**；全闭环仍待 FE 接线 Wasm 后复测 |
