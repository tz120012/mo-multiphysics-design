# Q4-9 冒烟记录 — 后端 artifacts GET 修复 tip `e9d8af6`（P09 Jobs/artifacts 补抽）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:42 Asia/Shanghai |
| 指派 tip | **`e9d8af6`**（`fix(api): artifacts GET fallback to /tmp/mo-opt + mount mo_femdata on api`） |
| tip 全 SHA | `e9d8af65db5d6a7e2e2208c59d6ca418c42ccf8e` |
| 前证缺口 tip | **`422b518`** @ `5112059`：compose artifacts **GET pareto → 404**（api 无 `mo_femdata` / 未设 `MO_OPT_WORKDIR`） |
| 祖先确认 | `git merge-base --is-ancestor e9d8af6 HEAD` → **0** |
| 仓库 HEAD（实测时） | `e9d8af6`（业务 tip 即 HEAD） |
| 执行 | Mo-测试；仅 `docs/qa/`；**未**改业务代码；**本轮未再 recreate**（Mo-后端/运维确认已完成） |
| 性质 | Motor 补抽：关闭 `422b518` 卷/ENV 缺口；**不重开** CLI tip `185b9d5`/`6118490`；**禁精度宣称** |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `e9d8af6` 为 HEAD 祖先（exit **0**） |
| pytest | `cd apps/api && .venv/bin/python -m pytest tests/test_optimize_jobs.py tests/test_job_artifacts.py -q` → **9 passed**, 2 warnings in ~1.5s |
| compose API | `http://127.0.0.1:8000`；`GET /health` → status=ok；db/redis ok |
| mo-api 容器 | Image `mo-platform-api`；Created/Started ≈ **2026-10-28 14:41 Asia/Shanghai**（UTC 06:41）；**healthy** |
| 挂载 | `mo-platform_mo_femdata` → `/var/mo/fem`（**RW**）；`touch` 写测 **WRITE_OK** |
| ENV（api） | `MO_OPT_WORKDIR=/var/mo/fem`；`MO_FEM_WORKDIR=/var/mo/fem`；`CELERY_ENABLED=0`；`SOLVER_OPT_PATH=/opt/mo/packages/solver-opt` |
| recreate | **本轮未执行**；Mo-后端/运维确认 recreate 已吃到挂载/ENV。照实记录意图命令：`sudo -n docker compose --env-file .env up -d --force-recreate api`（或 box overlay 等价；仅 api，未 down 全家桶） |
| 隔离 | 仅 `/workspace/mo-platform`；本轮**未**改 `apps/`/`packages/`/`docker-compose*` |

## 主证据：pytest

```bash
cd /workspace/mo-platform/apps/api
git merge-base --is-ancestor e9d8af6 HEAD   # exit 0
.venv/bin/python -m pytest tests/test_optimize_jobs.py tests/test_job_artifacts.py -q
# 9 passed, 2 warnings in ~1.52s
```

| 文件 | 结果 |
| --- | --- |
| `tests/test_optimize_jobs.py` | 含于合计 **9 passed**（与后端宣称一致） |
| `tests/test_job_artifacts.py` | 含于合计 **9 passed**（tip 新增/强化 artifacts resolve） |

## compose 实抽（补抽目标）

鉴权：`POST /api/v1/auth/login` `demo/demo` → Bearer。  
payload：`packages/solver-opt/fixtures/seed42_rf_pmsm_payload.json`（去掉顶层 `projectId`）+ `JobCreate{projectId, jobType:optimize, payload}`。

| # | 检查 | 实测 | 判定 |
| --- | --- | --- | --- |
| C1 | 422 空 payload | **422** `validation_error`「OptimizeJobPayload validation failed」 | **PASS** |
| C2 | POST optimize seed42 | **202** queued → poll **succeeded**；job `025cee9a-64ef-47f3-bc1d-3bd169433c63`；`resultRef=solver/optimize/jobs/025cee9a-…/manifest.json` | **PASS**（in-process；`CELERY_ENABLED=0`） |
| C3 | artifacts LIST | **200**；1 项：`results/optimize/025cee9a-…/pareto.json` `role=pareto` | **PASS** |
| C4 | artifacts GET pareto | **200** `application/json`；`seed=42`；`fronts` 有；`individuals`=8；`digest.paretoCount=8` | **PASS**（相对 `422b518` **缺口关闭**） |
| C5 | artifacts GET manifest | **200**；含 `status`/`nsga`/`summary`/`resultRef` | **PASS** |
| 落盘 | api 容器 | `/var/mo/fem/mems_shadow/results/optimize/{jid}/pareto.json` + `…/solver/optimize/jobs/{jid}/manifest.json` 存在；**无**依赖 `/tmp/mo-opt` | **PASS** |

### 对比前证 `422b518`（@ `5112059`）

| 项 | `422b518` 当时 | 本轮 @ `e9d8af6` |
| --- | --- | --- |
| api `mo_femdata` | **无** | **有**（RW `/var/mo/fem`） |
| `MO_OPT_WORKDIR` / `MO_FEM_WORKDIR` | **未设** | **`/var/mo/fem`** |
| artifacts GET pareto | **404** `artifact_not_found` | **200** |
| 结论 | compose 卷/ENV 缺口（不否决 pytest） | **缺口关闭** |

## 判定与口径

| 层 | 结论 |
| --- | --- |
| pytest | **PASS** — **9 passed** |
| compose 补抽 | **PASS**：POST succeeded+resultRef + LIST + **GET pareto/manifest 200** |
| vs `422b518` | artifacts GET **404 → 200**；卷/ENV 缺口**关闭** |
| 对 P09 状态 | **保持**「通过（CLI seed fixture）」**不重开**；备注追加 **Jobs/artifacts GET 补抽 PASS @ e9d8af6** |
| 禁止宣称 | **≤5% / ≤3%** 达标、帕累托真实最优、数值精度、**MVP** — 一律**不宣称** |

## 未做 / 遗留

- 未改 `CELERY_ENABLED`；本轮仍 **in-process**（与现网 api 默认一致）；Celery optimize 入队未本轮硬验。
- 未重开 / 重跑 CLI tip `6118490`/`185b9d5`。
- 未测 UI 优化入口；**未动 P05/P11** 状态（P05 另线浏览器抽测中）。
- 本轮**未**自行 recreate（运维已完成）；未 down 全家桶。

## 跟踪动作

- [Q4-验收跟踪](Q4-验收跟踪.md)：P09 状态保持；备注 + changelog 一行 @ `e9d8af6`。
- [Q4-冒烟清单](Q4-冒烟清单.md)：E1/E2 备注补抽；实测表追加本 tip。
