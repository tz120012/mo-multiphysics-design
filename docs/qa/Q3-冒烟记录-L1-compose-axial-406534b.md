# Q3 冒烟记录 — Q3-L1 compose AF axial（独立抽复测）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:48 Asia/Shanghai |
| 仓库 HEAD（实测时） | **`406534b`** |
| 关联 | Q3-L1（compose `mo-api` 曾未带齐 `axial_planes`）；对照 CLI tip **`f2a2e94`** / 记录 [Q3-冒烟记录-解析-axial-f2a2e94](Q3-冒烟记录-解析-axial-f2a2e94.md) |
| 执行 | Mo-测试执行员 |
| 入口 | **compose 容器 `mo-api`**（`:8000` → docker-proxy → 容器 uvicorn）；**禁止**本机 uvicorn 顶替 |
| 范围 | 仅 AF+PMSM compose API 路径；**不**宣称解析 ≤5% / FEM ≤3% |

## 环境（证明 `:8000` = compose 容器，非本机 uvicorn）

| 证据 | 结果 |
| --- | --- |
| `sudo docker ps` | `mo-api` **Up (healthy)**；`0.0.0.0:8000->8000/tcp`；Image=`mo-platform-api` |
| 监听者 | `ss -tlnp :8000` → **`docker-proxy`**（非宿主 `.venv` uvicorn） |
| 本机 uvicorn | `pgrep -af 'apps/api\|.venv.*uvicorn'` → **无** |
| 容器内包 | `docker exec mo-api ls …/axial_planes/` → 含 `pmsm.py` / `geometry.py` / `__init__.py`；`HAS_pmsm.py`；`SOLVER_ANALYTIC_PATH=/opt/mo/packages/solver-analytic` |
| 容器重建时刻 | Created/Started ≈ **2026-10-28 12:47:57 Asia/Shanghai**（UTC `2026-10-28T04:47:57Z`；运维无缓存重建后） |
| Health | `GET http://127.0.0.1:8000/health` → `status=ok`，db/redis `ok=true`，`version=1.0.0-draft` |
| 容器内 loopback | `docker exec mo-api` → `POST …/solver/analytic/solve?solver=mec` → **200**；`meta.solver=axial_planes`；同数值 |

> 对照 [Q3-冒烟记录-解析-axial-f2a2e94](Q3-冒烟记录-解析-axial-f2a2e94.md)：彼时镜像仅 README、AF → **400** `not_implemented`。本轮重建后 compose 路径可关 L1。

## Motor 硬口径

| # | 硬口径 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | 请求打到 **compose 容器 api**（非本机 uvicorn），端口惯例 `:8000` | docker-proxy + healthy `mo-api`；无宿主 venv uvicorn；容器内含 `axial_planes/pmsm.py`；loopback 同结果 | **PASS** |
| 2 | 鉴权后 POST analytic/solve（AF+PMSM），fixture `axial_pmsm` | `POST /api/v1/auth/login` demo → Bearer；`POST …/solver/analytic/solve?solver=mec` + `packages/solver-analytic/smoke/fixtures/axial_pmsm_request.json`；无鉴权 → **401** | **PASS** |
| 3 | **200**，`meta.solver=axial_planes`，T≈2.33、E≈24.405、`n_planes=4`（与 f2a2e94 CLI 量级一致） | 见下表；与 CLI 金标逐字段一致 | **PASS** |
| 4 | **不对标 ≤5%** | 本记录**未**勾选/宣称相对标杆 ≤5% | **遵守** |

### 关键字段（compose host→`:8000` 与容器 loopback 一致）

```json
{
  "schema_version": "0.0.0-gate0",
  "meta": {
    "solver": "axial_planes",
    "elapsed_ms": 2.43,
    "mock": false,
    "n_planes": 4
  },
  "torque_nm": 2.330476641855485,
  "back_emf_v_peak": 24.404694324719348
}
```

| 字段 | compose API | CLI f2a2e94 宣称 | 一致 |
| --- | --- | --- | --- |
| HTTP | **200** | （CLI exit 0） | — |
| `meta.solver` | `axial_planes` | `axial_planes` | 是 |
| `meta.mock` | `false` | `false` | 是 |
| `meta.n_planes` | `4` | `4` | 是 |
| `torque_nm` | `2.330476641855485` | ≈2.330 | 是 |
| `back_emf_v_peak` | `24.404694324719348` | ≈24.405 | 是 |

无 query 的 `POST …/solve`（自动路径）同样 **200** / `axial_planes` / 同数值。

### 命令摘要

```bash
cd /workspace/mo-platform
sudo docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'
pgrep -af 'apps/api|.venv.*uvicorn' || echo 'no host venv uvicorn'
sudo docker exec mo-api sh -c 'test -f /opt/mo/packages/solver-analytic/axial_planes/pmsm.py && echo HAS_pmsm.py'

BASE=http://127.0.0.1:8000/api/v1
FIXTURE=packages/solver-analytic/smoke/fixtures/axial_pmsm_request.json
curl -s -w '\nHTTP %{http_code}\n' -X POST "$BASE/solver/analytic/solve" \
  -H 'Content-Type: application/json' -d @"$FIXTURE"   # → 401

TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')
curl -s -w '\nHTTP %{http_code}\n' -X POST "$BASE/solver/analytic/solve?solver=mec" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d @"$FIXTURE"
```

## 未做 / 禁止宣称

- **未**勾选或宣称解析相对标杆 **≤5%** / FEM **≤3%**（仍待校准）。
- **未**改 `apps/` 业务代码；本记录仅文档。
- **未**挡并行 fem stub 工作；仅关 Q3-L1。

## 跟踪变更

| 项 | 变更 |
| --- | --- |
| Q3-L1 | **跟踪中（运维自报绿）→ 已消化**（测试独立抽复测 PASS） |
| Q3-P01 备注 | 补记 compose AF 抽复测绿；仍**未**宣称 ≤5% |
| P02–P07 / Q3-L2 | 本轮不改 |

## 结论

| 项 | 结论 |
| --- | --- |
| Q3-L1 compose AF axial | **PASS** |
| 对标 ≤5% | **未宣称**（禁止） |
