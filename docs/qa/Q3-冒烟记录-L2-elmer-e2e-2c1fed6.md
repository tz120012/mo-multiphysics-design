# Q3 冒烟记录 — L2 / P03 真 Elmer heat-proxy E2E tip `2c1fed6`（+ 后端 `781c09b`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 13:10 Asia/Shanghai |
| 基线 tip（FEM） | **`2c1fed6`**（`feat(fem): true Elmer E2E path A — worker image + gmsh/ElmerGrid/ElmerSolver`） |
| 后端 tip | **`781c09b`**（`feat(api): gate FEM jobs on MO_FEM_DRY_RUN; call solver-fem.run_job when 0`） |
| 仓库 HEAD（实测时） | **`2c1fed6`**（工作区干净；两 tip 均为 HEAD / 祖先） |
| 执行 | Mo-测试执行员（**独立实测**；非抄有限元自报） |
| 入口 | compose **box overlay** + `CELERY_ENABLED=1` + profiles `worker,fem`；临时 `MO_FEM_DRY_RUN=0` 抽 E2E 后已改回 **1** |
| 范围 | Q3-L2 / P03 真 Elmer **heat-proxy** 调度链（gmsh→ElmerGrid→ElmerSolver）；RF 2D + AF 3D 各一单 |
| 禁止 | **未**宣称 FEM ≤3% / 解析 ≤5%；**非**磁静力学电机解；**未**代签；**仅**改 `docs/qa/` |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `git merge-base --is-ancestor 2c1fed6 HEAD` → 0；`781c09b` → 0 |
| HEAD | `git rev-parse --short HEAD` → **`2c1fed6`**；`git status` 干净（业务已入库，**非** WIP） |
| rebuild | `sudo docker compose … --profile fem build worker-fem` → Built（镜像含 Elmer；Dockerfile.worker path A） |
| dry-run=0 | `sudo env MO_FEM_DRY_RUN=0 CELERY_ENABLED=1 docker compose … up -d --force-recreate --no-deps worker-fem` |
| printenv | `docker exec mo-worker-fem printenv MO_FEM_DRY_RUN` → **0**（测中）→ 测后 **1** |
| 工具链 | worker-fem：`ElmerSolver` **v 26.2**；`gmsh`；`ElmerGrid` 均有路径 |
| API | recreate `CELERY_ENABLED=1`；`GET /health` → status=ok；db/redis ok |
| 鉴权 | `POST /api/v1/auth/login` demo/demo → Bearer |
| 测完 | 已 `MO_FEM_DRY_RUN=1` recreate worker-fem；`printenv` → **1** |

## Motor 硬口径（本轮）

| # | 硬口径 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | 基线 tip `2c1fed6` + 后端 `781c09b` | 均为 HEAD / 祖先；HEAD=`2c1fed6` | **PASS** |
| 2 | Jobs `jobType=fem` 入队 → succeeded | RF/AF 均 202→queued→succeeded + resultRef | **PASS** |
| 3 | manifest `dryRun=false` + `elmerExit=0` | RF/AF 均 false / 0；notes 含 ElmerSolver OK (heat-proxy) | **PASS**（heat-proxy） |
| 4 | RF 2D + AF 3D 各至少一单 | RF `17d711f6-…`；AF `98279d72-…` | **PASS** |
| 5 | 不宣称 ≤3% | notes/`pending_calibration`；本记录未勾 ≤3% | **遵守** |
| 6 | 测完 DRY_RUN 改回 1 | printenv=1；stub 对照 dryRun=true | **PASS** |

## 鉴权 / 校验

| 用例 | 结果 | 判定 |
| --- | --- | --- |
| 无 Authorization POST `/jobs` | **401** unauthorized | PASS |
| fem + `payload:{}` | **422**；missing topology/machineType/dim/solverKernel/meshProfile/operatingPoint/materials | PASS |

## 真 Elmer 段（临时 `MO_FEM_DRY_RUN=0`）

| 用例 | jobId | 耗时（API created→updated） | Celery 任务 | manifest 要点 | 判定 |
| --- | --- | --- | --- | --- | --- |
| RF 2D PMSM | `17d711f6-48ac-4afb-9632-85f45b365f2d` | ~3.39 s（worker ~0.66 s） | `run_fem_job` succeeded | `dryRun=false`；`elmerExit=0`；`pending_calibration=true`；notes=`ElmerSolver OK (heat-proxy Q3 E2E); pending_calibration — do NOT claim FEM ≤3%` | **PASS** heat-proxy |
| AF 3D PMSM | `98279d72-f196-4307-9572-b456ad8f13ce` | ~3.14 s（worker ~0.71 s） | `run_fem_job` succeeded | 同上；topology=AF dim=3d | **PASS** heat-proxy |

resultRef（两单）：`solver/fem/jobs/{id}/manifest.json`

### RF manifest 摘要

```json
{
  "jobId": "17d711f6-48ac-4afb-9632-85f45b365f2d",
  "status": "succeeded",
  "solverKernel": "elmer",
  "topology": "RF",
  "machineType": "PMSM",
  "dim": "2d",
  "scalars": {
    "torqueNm": 0.0,
    "dryRun": false,
    "pending_calibration": true,
    "elmerExit": 0
  },
  "notes": "ElmerSolver OK (heat-proxy Q3 E2E); pending_calibration — do NOT claim FEM ≤3%"
}
```

### AF manifest 摘要

```json
{
  "jobId": "98279d72-f196-4307-9572-b456ad8f13ce",
  "status": "succeeded",
  "topology": "AF",
  "dim": "3d",
  "scalars": {
    "dryRun": false,
    "pending_calibration": true,
    "elmerExit": 0
  },
  "notes": "ElmerSolver OK (heat-proxy Q3 E2E); pending_calibration — do NOT claim FEM ≤3%"
}
```

### 管道证据（非 stub）

- 作业目录含 `solve/case.sif`、`mesh.msh`、`out/elmer_pipeline.log`
- RF 日志：`gmsh … -2` → `ElmerGrid 14 2` → `ElmerSolver`；`heat equation`；`*** Elmer Solver: ALL DONE ***`
- AF 日志：`gmsh … -3` → `ElmerGrid` → `ElmerSolver`；`heat equation`；`ALL DONE`
- **口径**：heat-proxy E2E（调度链），**不是**磁静力学电机解；**禁止**宣称 ≤3%

## 可选对照（`MO_FEM_DRY_RUN=1` 改回后）

| 用例 | jobId | 结果 | 判定 |
| --- | --- | --- | --- |
| RF stub 回归 | `e39ca990-ef65-4ac9-834b-c1b3d7ea8d45` | succeeded；`scalars.dryRun=true`；notes=`API stub; …`；无 `elmerExit` | **PASS**（回归不破） |

## 未做 / 禁止宣称

- **未**宣称或勾选 FEM **≤3%** / 解析 **≤5%**。
- **未**做磁静力学电机校核；**未**代签开 Q4 / P07。
- 本轮判定为 **heat-proxy 调度链 PASS**，不等于数值达标。

## 跟踪建议（对齐 Motor）

| 项 | 建议 |
| --- | --- |
| Q3-P03 | **通过（真 Elmer heat-proxy 调度）**（叠加既有 stub/镜像）；证据本记录；仍注明非磁静力学、未对标 ≤3% |
| Q3-L2 | **已消化（heat-proxy E2E）**：worker-fem 含 Elmer + `MO_FEM_DRY_RUN=0` → `dryRun=false`/`elmerExit=0`；默认 dry-run=1 仍 stub |
| Q3-P04 / P05 | 可升「通过（heat-proxy E2E）」或维持模板 + 本记录交叉引用（产品裁定） |
| ≤3% | **仍待校准**；禁止勾选 |

## 结论

| 项 | 结论 |
| --- | --- |
| 祖先 / HEAD `2c1fed6` | **PASS** |
| worker-fem Elmer 工具链 | **PASS**（v26.2 + gmsh + ElmerGrid） |
| RF heat-proxy E2E | **PASS**（`17d711f6-…`；dryRun=false；elmerExit=0） |
| AF heat-proxy E2E | **PASS**（`98279d72-…`；dryRun=false；elmerExit=0） |
| 401 / 422 | **PASS** |
| DRY_RUN=1 回归 + 测完改回 | **PASS** |
| ≤3% / 磁静力学 | **未宣称**（禁止） |
