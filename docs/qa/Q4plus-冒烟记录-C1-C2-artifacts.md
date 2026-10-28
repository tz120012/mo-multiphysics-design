# Q4+ 冒烟记录 — C1/C2（Jobs artifacts = L4 / Q4+-3）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 15:30 Asia/Shanghai |
| 业务 tip | **`6144f91`**（`fix(api): Q4+-3 lock Jobs artifacts as L4 single-file + OpenAPI`） |
| tip 全 SHA | `6144f9163e7d9f505ad444642a188c84f90e41cc` |
| 裁决 tip | **`83d2e6e`**（`docs(arch): Q4+-3 mems/artifacts 收口裁决`；Motor **F5=A**） |
| 产品叠层 | **`71aa75b`**（已 push；本 tip 之上） |
| 祖先确认 | `git merge-base --is-ancestor 6144f91 HEAD` → **0**；`83d2e6e` 同为祖先 |
| 仓库 HEAD（写记录时） | 以本 commit 证据 tip 为准 |
| 执行 | Mo-测试；**仅** `docs/qa/`；**未**改业务代码；**未** push |
| 性质 | Motor 交测 Q4+-3；Jobs-artifacts-only；**不做** mems/files；FE `source=job-artifacts` **另线** |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `6144f91` / `83d2e6e` 均为 HEAD 祖先 |
| pytest 环境 | `apps/api/.venv/bin/python`（Python 3.13 venv） |
| pytest | `cd apps/api && .venv/bin/python -m pytest tests/test_job_artifacts.py tests/test_optimize_jobs.py -q` → **10 passed**, 2 warnings in ~1.81s |
| live API | `http://127.0.0.1:8000`；`GET /health` → status=ok；db/redis ok |
| 隔离 | 仅 `/workspace/mo-platform`；本轮**未**改 `apps/`/`packages/`；**未**强制重建镜像（tip 源码-only） |

## 主证据：pytest（必做）

```bash
cd /workspace/mo-platform/apps/api
.venv/bin/python -m pytest tests/test_job_artifacts.py tests/test_optimize_jobs.py -q
# 10 passed, 2 warnings in 1.81s
```

| 文件 | 结果 |
| --- | --- |
| `tests/test_job_artifacts.py` | 含于合计 **10 passed**（tip 强化 L4/Q4+-3 resolve + zip fallback） |
| `tests/test_optimize_jobs.py` | 含于合计 **10 passed** |

## OpenAPI / 源码注记抽查（必做）

权威契约注记路径：**`docs/drafts/openapi-v1.yaml`**（`/jobs/{jobId}/artifacts` 与 `.../artifacts/{artifactPath}`）。

要点摘录（非全引）：

1. **Jobs artifacts GET = L4 / Q4+-3 精简结果单文件读**；工程包仍走整包 mems。
2. **`GET .../mems/files/{path}` 为 Q4+-3b**（Motor F5=A 默认推迟），**本门不提供 / 非硬项**。
3. 本路由关闭 Q3-L4「无 mems 单文件 GET」对 `/field`（有 jobId 时）的缺口叙述：canonical 单文件通道 = list + get。
4. 读的是 F1 精简件（manifest / scalars / slice / preview / pareto），**非全场 VTU**。
5. mems 下载注记：**整包 I/O only**；精简单文件读走 Jobs artifacts。

源码对齐：

- `apps/api/app/routers/jobs.py`：summary/docstring 含 **L4/Q4+-3**；get 明确 `mems/files` = Q4+-3b。
- `apps/api/app/artifacts_resolve.py` 文首：Jobs GET 为主；`GET .../mems/files` deferred（Q4+-3b）。

live `:8000/openapi.json`：路径存在且 **无** `mems/files`；summary 仍为较旧「F1」文案（**未** recreate 镜像吃 tip——源码-only，不否决仓库注记）。

## 可选 compose / live API（卷沿用 e9d8af6）

本 tip **源码-only**，**未**强制重建镜像。live `:8000` 可测则抽：

| # | 检查 | 实测 | 判定 |
| --- | --- | --- | --- |
| L1 | auth demo/demo | Bearer 签发 | **PASS** |
| L2 | POST optimize seed42 | **202** → poll **succeeded**；job `8d6bba20-…`；`resultRef=solver/optimize/jobs/…/manifest.json` | **PASS**（in-process） |
| L3 | artifacts LIST | **200**；1 项 `results/optimize/…/pareto.json` `role=pareto` | **PASS** |
| L4 | artifacts GET pareto | **200**；含 `seed=42` / `fronts` | **PASS** |
| L5 | artifacts GET manifest | **200** | **PASS** |

docker.sock 本环境无权限（`permission denied`）；未 recreate；功能连续性沿用历史卷/`MO_*_WORKDIR` 口径（`e9d8af6`）。**不**因镜像未含 tip 文案否决 list/get **200**。

## C1 / C2 判定

| ID | 结论 | 说明 |
| --- | --- | --- |
| Q4+-C1 | **PASS** | F5=A 下本门 = Jobs artifacts L4 精简单文件权威；**无**独立 mems/files；pytest 10 + OpenAPI 注记 + live list/get 200 |
| Q4+-C2 | **部分 PASS（后端）** | 后端 OpenAPI/router 注记锁定；**FE `source=job-artifacts` 另线——勿标 FE 已关** |

## 关项口径（跟踪必须）

| 项 | 写法 |
| --- | --- |
| Q3-L4 **子项**「无 mems 单文件 GET」（field/artifacts） | **可关**（Jobs artifacts canonical @ `6144f91` / `83d2e6e`） |
| Q3-L4 **整行** | **不可关**（余 磁静力学 / FE job-artifacts；live/AF Wasm 已随 Q4+-4 通过可记部分消化） |
| Q4+-3 | **通过（后端）**；FE 另线未关；mems/files=Q4+-3b |
| 禁止宣称 | **≤5% / ≤3%** 达标、**MVP 已达成** — 一律**不宣称**；**不代签** |

## 跟踪 / 清单变更

| 项 | 变更 |
| --- | --- |
| [Q4plus-冒烟清单](Q4plus-冒烟清单.md) | C1→**PASS**；C2→**部分 PASS（后端）**；F1/F2 **不勾** |
| [Q4plus-验收跟踪](Q4plus-验收跟踪.md) | Q4+-3→**通过（后端）**；遗留 Q3-L4 子项可关 / 整行不可关 |
| [Q3-验收跟踪](Q3-验收跟踪.md) / [Q4-验收跟踪](Q4-验收跟踪.md) | Q3-L4 行同步子项可关口径 |

## 未做

- **未**实现 / 冒烟 `GET .../mems/files/{path}`（Q4+-3b）。
- **未**标 FE `source=job-artifacts` 已关。
- **未**强制重建 api 镜像；live OpenAPI summary 未吃 tip 文案。
- **未**勾 F1/F2；**未**宣称 MVP；**未**代签。

---

**产品确认（Mo-产品）**：同意 C1 PASS / C2 后端 PASS → Q4+-3 **通过（后端）**；FE `source=job-artifacts` **另线未关**；`mems/files`=Q4+-3b；**仍禁勾 ≤5%/≤3%**；**不开宣称 MVP**。业务 tip **`6144f91`**。

---

*证据 tip：本 commit short SHA；业务对照 `6144f91` @ 裁决 `83d2e6e`。*
