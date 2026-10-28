# Q4-9 冒烟记录 — 后端 optimize Jobs tip `5112059`（P09 Jobs 增强补充）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:35 Asia/Shanghai |
| 指派 tip | **`5112059`**（`feat(api): Q4-9 optimize Jobs 接 solver-opt NSGA（Celery/in-process）`） |
| tip 全 SHA | `5112059c77030b7be86015fee509db9d2e975fbc` |
| 运维叠 tip | **`dca1803`**（worker `-Q celery,optimize` + bake solver-opt）；**`14d6113`**（`MO_OPT_WORKDIR` 回退 `mo_femdata`） |
| 祖先确认 | `5112059` / `dca1803` / `14d6113` 均为 HEAD 祖先（`merge-base --is-ancestor` → 0） |
| 仓库 HEAD（实测时） | `9a377e9`（含上述 tip） |
| 执行 | Mo-测试；仅 `docs/qa/`；**未**改业务代码 |
| 性质 | Motor 补充交测：P09 **Jobs 增强**；**不重开**已关 CLI tip `185b9d5`/`6118490`；**禁精度宣称** |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `git merge-base --is-ancestor 5112059 HEAD` → **0**；同检 `dca1803`/`14d6113` → **0** |
| 主证据 | `cd apps/api && .venv/bin/python -m pytest tests/test_optimize_jobs.py -q` |
| compose API | `http://127.0.0.1:8000`；`GET /health` → status=ok；db/redis ok |
| OpenAPI jobs | 含 `POST /api/v1/jobs`、`GET …/{id}`、`POST …/cancel`、`GET …/artifacts`、`GET …/artifacts/{path}` |
| mo-worker | `CELERY_ENABLED=1`；`-Q celery,optimize`（active_queues 含 **optimize**）；`SOLVER_OPT_PATH=/opt/mo/packages/solver-opt`；`MO_OPT_WORKDIR=/var/mo/fem`（volume `mo_femdata`） |
| mo-api（现网） | **`CELERY_ENABLED=0`**（compose 默认）；`SOLVER_OPT_PATH` 已 bake；**未**设 `MO_OPT_WORKDIR`；**无** `mo_femdata` mount → 本轮 live POST 走 **in-process degrade**，**未**入 Celery `optimize` 队列 |
| 隔离 | 仅 `/workspace/mo-platform`；本轮**未**改 `apps/`/`packages/`/`docker-compose*` |

## 主证据：pytest（必跑）

```bash
cd /workspace/mo-platform/apps/api
.git 祖先：git merge-base --is-ancestor 5112059 HEAD   # exit 0
.venv/bin/python -m pytest tests/test_optimize_jobs.py -q
# 4 passed, 2 warnings in ~1.4s
```

| # | 用例 | 覆盖 | 判定 |
| --- | --- | --- | --- |
| 1 | `test_optimize_missing_fields_422` | 空 payload → **422** `validation_error` / OptimizeJobPayload | **PASS** |
| 2 | `test_optimize_seed42_happy_path_artifacts` | POST → poll **succeeded**；`resultRef=solver/optimize/jobs/{id}/manifest.json`；manifest+pareto 落盘；artifacts list + GET pareto | **PASS** |
| 3 | `test_optimize_without_base_solve_uses_fixture` | 省略 `baseSolveRequest` → fixture 默认仍 **succeeded** | **PASS** |
| 4 | `test_optimize_cancel` | cancel → **cancelled**；幂等再 cancel；未知 id **404** | **PASS** |

> TestClient 路径：`CELERY_ENABLED=0` + `MO_OPT_WORKDIR` tmp → **in-process**（与单测设计一致；覆盖 cancel / artifacts GET 全表）。

## 可选：compose 抽测（不否决；Celery 优先意图 vs 现网）

意图：运维 tip 后优先 Celery（`mo-worker` 吃 `optimize`）。**现网 `mo-api` `CELERY_ENABLED=0`**，故本轮 live 实际为 **in-process degrade**；worker 队列/路径已确认就绪，但 API **未入队**。

鉴权：`POST /api/v1/auth/login` `demo/demo` → Bearer。

| # | 检查 | 实测 | 判定 |
| --- | --- | --- | --- |
| C1 | 422 空 payload | **422** `validation_error`「OptimizeJobPayload validation failed」 | **PASS** |
| C2 | POST optimize seed42 | **202** queued → poll **succeeded**；`resultRef=solver/optimize/jobs/51e75b78-…/manifest.json`（job `51e75b78-b286-4215-9de6-fb64caa145fa`） | **PASS**（in-process） |
| C3 | artifacts LIST | **200**；`artifacts[]` 含 `results/optimize/…/pareto.json` `role=pareto` | **PASS** |
| C4 | artifacts GET pareto | **404** `artifact_not_found`（提示需共享 `MO_OPT_WORKDIR`/`MO_FEM_WORKDIR`）；api 容器内文件在 `/tmp/mo-opt/mems_shadow/…` 已落盘，但 resolve 未命中；api **无** `/var/mo/fem` 卷 | **FAIL（compose 卷/ENV 不齐；不否决 pytest）** |
| C5 | cancel | POST cancel → **200** `cancelled`；poll **cancelled**（job `e73ce6ba-…` / 同路径复测） | **PASS** |
| C6 | Celery 入队 | api `CELERY_ENABLED=0`；worker 有 optimize 队列但本轮 job **未**写到 `/var/mo/fem` | **未走通 Celery**（环境配置；非业务 tip 否决） |

## 判定与口径

| 层 | 结论 |
| --- | --- |
| pytest（主证据） | **PASS（Jobs 增强）** — 4/4 |
| compose 抽测 | **部分可达**：POST/422/cancel/LIST **PASS**；artifacts GET **FAIL**（workdir/卷）；Celery 路径 **未实跑**（api `CELERY_ENABLED=0`） |
| 对 P09 状态 | **保持**「通过（CLI seed fixture）」**不重开**；备注追加 **Jobs 增强补充 PASS @ 5112059**（pytest）；compose 遗留不挡本项 |
| 禁止宣称 | **≤5% / ≤3%** 达标、帕累托真实最优、数值精度、**MVP** — 一律**不宣称** |

## 未做 / 遗留

- 未把现网 `mo-api` 改为 `CELERY_ENABLED=1` 或挂 `mo_femdata`（属运维重启/重配；本员仅 docs）。
- 未重跑 / 重开 CLI tip `6118490`/`185b9d5`。
- 未测 UI 优化入口；未动 P11 / P08 交测。

## 跟踪动作

- [Q4-验收跟踪](Q4-验收跟踪.md)：P09 状态保持 **通过（CLI seed fixture）**；备注 + changelog/观察说明追加 Jobs 补充 @ `5112059`（叠运维 `dca1803`/`14d6113`）。
- [Q4-冒烟清单](Q4-冒烟清单.md)：E1/E2 保留 CLI PASS；实测表追加本 tip（Jobs pytest）。
