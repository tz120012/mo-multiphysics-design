# Q3 冒烟记录 — L2 / P04 / P05 tip `a44a4fb`（+ 运维联调 `c9365a4`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:59 Asia/Shanghai |
| 指派 tip | **`a44a4fb`**（`feat(fem): Q3-L2 Elmer Dockerfile + RF/AF templates`） |
| 配合 tip | **`c9365a4`**（`docs(ops): Q3-L2 dry-run=0 联调路径 + make up-fem-box`） |
| 仓库 HEAD（实测时） | `c9365a4`（两 tip 均为 HEAD 祖先；HEAD=`c9365a4`） |
| 执行 | Mo-测试执行员（**独立实测**；非抄运维自报） |
| 入口 | compose **box overlay** + `CELERY_ENABLED=1` + profiles `worker,fem`；默认 `MO_FEM_DRY_RUN=1`；临时 `=0` 抽 E2E 后已改回 `1` |
| 范围 | Q3-L2 镜像工具链 + P04/P05 模板 + dry-run 单测/入队；真 Elmer 端到端抽测（如实） |
| 禁止 | **未**宣称解析 ≤5% / FEM ≤3%；**未**代签；**未**改 `apps/` 业务代码 |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `git merge-base --is-ancestor a44a4fb HEAD` → 0；`c9365a4` → 0 |
| HEAD | `git rev-parse --short HEAD` → **`c9365a4`** |
| 独立镜像 | `mo-fem:q3-l2` id `d1fee63d4e36` ~1.07GB（本机复用；`docker run --rm mo-fem:q3-l2 ElmerSolver` 可见 v26.2） |
| compose fem | 运维重建后 `mo-platform-fem:latest` id **`3bc3b90c062c` ~1.07GB**（**非**旧 stub 83MB）；label `org.mo.stage=q3-l2-elmer` |
| 宿主机 Elmer | `which ElmerSolver` → **空**（禁止宿主机安装；符合口径） |
| 起栈 | box overlay；`CELERY_ENABLED=1` recreate `mo-api`；`mo-worker-fem` Up；`MO_FEM_DRY_RUN=1`（默认） |
| 健康 | `GET /health` → `status=ok`；db/redis `ok=true` |
| 鉴权 | `POST /api/v1/auth/login` `demo/demo` → Bearer |
| 未改 | **未**改 `apps/`；本记录仅 `docs/qa/`；测完已将 `MO_FEM_DRY_RUN` **改回 1** |

## Motor 硬口径

| # | 硬口径 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | 祖先 a44a4fb（及 c9365a4） | 均为 HEAD 祖先；HEAD=`c9365a4` | **PASS** |
| 2 | P04 模板 `rf_pmsm_2d` | 含 `case.sif` / `mesh.geo` / `README.md`；`resolve_template(RF,PMSM,2d)` → `rf_pmsm_2d` | **PASS** |
| 3 | P05 模板 `af_pmsm_3d` | 同上三文件；`resolve_template(AF,PMSM,3d)` → `af_pmsm_3d` | **PASS** |
| 4 | dry-run 单测 | `cd packages/solver-fem && python3 -m unittest tests.test_dry_run -v` → **OK**（1 test）；另对 AF 调 `run_job(..., dry_run=True)` → 准备目录含 templates + `manifest.json`（`scalars.dryRun=true`） | **PASS** |
| 5 | Q3-L2 镜像内 Elmer | `docker exec mo-fem`：`ElmerSolver` **v 26.2**；`gmsh` **4.8.4**；`getdp` **3.2.0**；无 case 时缺 `ELMERSOLVER_STARTINFO` → STOP 1（**预期**）；宿主机无 Elmer | **PASS** |
| 6 | compose 真工具链 | `mo-fem` 用 1.07GB `q3-l2-elmer` 镜像（非 83MB stub）；容器内 `which ElmerSolver` 有路径 | **PASS** |
| 7 | API dry-run 作业 | 缺 payload → **422**（missing topology…）；完整 RF payload → **202** → **succeeded**；`resultRef=solver/fem/jobs/{id}/manifest.json`；`scalars.dryRun=true`（`MO_FEM_DRY_RUN=1`） | **PASS**（dry-run） |
| 8 | 真 Elmer E2E | 见下「真 Elmer 段」——**未通**（勿假冒） | **未通 / 部分** |

### dry-run 段（`MO_FEM_DRY_RUN=1`）

| 用例 | 结果 | 判定 |
| --- | --- | --- |
| 无 Authorization POST `/jobs` | **401** unauthorized | PASS |
| fem + `payload:{}`（有 projectId） | **422**；missing 含 topology/machineType/dim/solverKernel/meshProfile/operatingPoint/materials | PASS |
| fem 省略 payload | **422** 同上 | PASS |
| RF 完整 payload | job `eb77e834-76fa-496d-bff5-2f9f4ad43406`：**succeeded**；resultRef 匹配；worker 日志 `app.tasks.fem.run_fem_job … succeeded`；manifest `dryRun=true`；notes 含 stub | PASS（dry-run） |

manifest 摘要（dry-run job `eb77e834-…`）：

```json
{
  "jobId": "eb77e834-76fa-496d-bff5-2f9f4ad43406",
  "status": "succeeded",
  "solverKernel": "elmer",
  "topology": "RF",
  "machineType": "PMSM",
  "dim": "2d",
  "scalars": {
    "torqueNm": 0.0,
    "dryRun": true,
    "pending_calibration": true,
    "notes": "API stub; Elmer/GetDP run only in FEM worker/container"
  }
}
```

### 真 Elmer 段（临时 `MO_FEM_DRY_RUN=0`，测完已改回 1）

按 `docs/deploy-local.md` / tip `c9365a4` 配方 recreate `worker-fem`；`printenv MO_FEM_DRY_RUN` 曾为 **0**，测后已恢复 **1**。

| 检查 | 实测 | 结论 |
| --- | --- | --- |
| worker-fem 内 Elmer | `command -v ElmerSolver` → **NO_ELMER**（worker 镜像无工具链；工具链在 `mo-fem` sidecar） | 工人无 Elmer 二进制 |
| API 作业（dry=0） | job `dc19ce8b-…` 仍 **succeeded** + resultRef；manifest **仍** `dryRun=true` / notes=API stub；~0.08s 完成；**无** ElmerSolver 进程痕迹 | **仍 stub**——`apps/api/app/tasks/fem.py` 固定 `build_stub_manifest`，**不读** `MO_FEM_DRY_RUN`，不调 `packages/solver-fem.run_job` |
| `run_job(dry_run=False)` @ `mo-fem` | 容器内有 Elmer；返回层 `dryRun=false`，但实现仍只调 `write_dry_run_artifacts`；manifest notes=`dry-run stub; no host Elmer/GetDP/Gmsh`；**未** subprocess 调 ElmerSolver | **求解路径未接线** |

> **口径**：镜像有 Elmer（L2 工具链 PASS）；**作业路径仍 dry-run/stub**——**不要**假冒真 Elmer 求解 PASS。

## 未做 / 禁止宣称

- **未**宣称或勾选解析 **≤5%** / FEM **≤3%**。
- **未**做 Q3 全量签字包；**未**代签开 Q4。
- **未**改产品未测项状态列以外内容；真 Elmer 求解 / worker↔sidecar 调用链后置。
- 本轮 **不**把「镜像有 Elmer」写成「真求解 PASS」。

## 跟踪变更（建议）

| 项 | 变更 |
| --- | --- |
| Q3-L2 | **部分消化**：Dockerfile + compose 真镜像（Elmer 26.2 / gmsh / getdp）**PASS**；作业仍 stub dry-run → **真 Elmer E2E 未通**，残余跟踪 |
| Q3-P04 | **通过（模板/dry-run）**；真 Elmer 求解未通（备注） |
| Q3-P05 | **通过（模板/dry-run）**；真 Elmer 求解未通（备注） |
| Q3-P03 有限元侧 | 镜像工具链 **PASS**；Celery 入队仍 stub；真 Elmer 调度 **未通** |

## 结论

| 项 | 结论 |
| --- | --- |
| L2 镜像工具链 | **PASS**（compose `mo-fem` 1.07GB；Elmer 26.2 / gmsh 4.8.4 / getdp 3.2.0；宿主机无 Elmer） |
| P04 模板 | **PASS** |
| P05 模板 | **PASS** |
| dry-run 单测 + 包内 AF dry-run | **PASS** |
| compose/API dry-run 入队 | **PASS**（422 / 202→succeeded / resultRef / dryRun=true） |
| 真 Elmer E2E | **未通**（worker stub + `run_job` 未调 ElmerSolver；dry=0 仍 dryRun manifest） |
| ≤3% / ≤5% | **未宣称**（禁止） |
