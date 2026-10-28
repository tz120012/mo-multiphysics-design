# Q3-L4 冒烟记录 — 后端 jobs artifacts tip `9ca055a`

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:22 Asia/Shanghai |
| 指派 tip | **`9ca055a`**（`feat(api): L4 jobs artifacts 最小可读（F1 worker 盘 / resultRef）`） |
| 仓库 HEAD（实测时） | `e89639b`（`9ca055a` 为祖先） |
| 执行 | Mo-测试（**独立实测**；仅 `docs/qa/`；**未**改 `apps/`） |
| 范围 | `GET …/artifacts` list + `GET …/artifacts/{path}` 单文件；缺 manifest / 坏路径 404；鉴权；**不做 UI**；**不**宣称 ≤3% |
| 与 Q4 | 并行于 Q4 骨架（产品 tip **`227211b`**：P01–P10 进行中 / P11 未开始）；本 tip 消化 Q3-L4 **mems/artifacts API** 段；FE 接线后 UI 闭环；本轮**未**改 P01–P10 状态 |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `git merge-base --is-ancestor 9ca055a HEAD` → **0**（通过） |
| tip 全 SHA | `9ca055a7c4b881f6bfa5ca7fc9035e6e67f8305e` |
| 单元测试 | `cd apps/api && .venv/bin/python -m pytest tests/test_job_artifacts.py -q` → **3 passed**（0.81s；1 Starlette/httpx deprecation warning） |
| compose `mo-api:8000` | **镜像尚未含本 tip**：`GET /openapi.json` 仅有 `/api/v1/jobs`、`/api/v1/jobs/{job_id}`；对 `…/artifacts` 无论鉴权均 **HTTP 404** `code=error`「Not Found」（路由未注册）。本轮**未**重建 api 镜像（成本高；pytest/TestClient 全绿为准） |
| 实跑载体 | **FastAPI TestClient**（本机 `apps/api` 源码 @ HEAD，含 tip）；鉴权 `demo/demo` Bearer；`CELERY_ENABLED=0`；临时 `MO_FEM_WORKDIR` |
| 未改 | **未**改 `apps/`；本记录 + 跟踪备注仅 `docs/qa/` |

> **口径**：API 形状与错误码以源码 `app/artifacts_resolve.py` + `app/routers/jobs.py` + pytest 为准。compose 实 curl 待重建含 `9ca055a` 的 `mo-api` 后再补；不否决本轮「API 形状」判定。

## Motor 硬口径（对齐）

| # | 硬口径 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | `GET /api/v1/jobs/{id}/artifacts` list | TestClient：磁盘 `mems_shadow` + `resultRef` → **200**；`jobId`/`resultRef`/`artifacts[]`（含 `role=scalars`） | **PASS** |
| 2 | `GET /api/v1/jobs/{id}/artifacts/{path}` 单文件 | 同盘 `scalars.json` → **200** `application/json` `{"ok":true}`；manifest 路径亦可 **200** | **PASS** |
| 3 | 缺 manifest → **404** + **`manifest_not_found`** | succeeded job、无盘无 payload.manifest → **404** `code=manifest_not_found`（router 原文） | **PASS** |
| 4 | 坏路径 / 无文件 | 路径穿越 `../etc/passwd` → **404**（TestClient；路由层未命中或拒绝）；缺文件 → **404** `code=artifact_not_found` | **PASS**（照实） |
| 5 | 鉴权 | `demo/demo` login → Bearer；无 Authorization → **401** `unauthorized` | **PASS** |
| 6 | stub 空 artifacts | payload 嵌入 `artifacts=[]` → list **200** + 空数组（非错误） | **PASS**（pytest + 补跑） |

### pytest 摘要

```text
apps/api$ .venv/bin/python -m pytest tests/test_job_artifacts.py -q
3 passed, 1 warning in 0.81s
```

覆盖：`test_list_and_get_from_mems_shadow`、`test_list_from_embedded_manifest_empty_artifacts`、`test_job_missing_404`（job 缺失 → `not_found`）。

### TestClient 补跑摘要（demo/demo）

| 用例 | HTTP / code | 判定 |
| --- | --- | --- |
| 无 Authorization GET artifacts | **401** `unauthorized` | PASS |
| login `demo`/`demo` | **200** `accessToken` | PASS |
| job 不存在 | **404** `not_found` | PASS |
| succeeded 无 manifest | **404** `manifest_not_found` | PASS |
| list（mems_shadow） | **200** + 1 artifact `role=scalars` | PASS |
| GET scalars 相对路径 | **200** JSON | PASS |
| GET 不存在文件 | **404** `artifact_not_found` | PASS |
| stub `artifacts=[]` | **200** `artifacts: []` | PASS |

### compose `:8000` 抽检（可选；镜像落后）

| 用例 | 结果 | 说明 |
| --- | --- | --- |
| OpenAPI 含 artifacts | **否** | 仅 jobs 两路径 |
| `GET …/artifacts`（有/无 Bearer） | **404** `error` Not Found | 路由未进镜像；**不**否决 API 形状（pytest 已覆盖有盘场景） |
| 已有 succeeded FEM dry-run list | **未**对 compose 做有效 list | worker 盘/镜像均未含本 tip；待重建后再试 |

## 源码错误码对照（照实）

| 场景 | HTTP | `code`（扁平响应） |
| --- | --- | --- |
| 无 Bearer | 401 | `unauthorized` |
| job 不存在 | 404 | `not_found` |
| job 在、manifest 无处可读 | 404 | **`manifest_not_found`** |
| 合法相对路径但文件不可解析 | 404 | `artifact_not_found` |
| 路径非法 / 穿越（normalize 失败） | 400 | `bad_path`（router；部分穿越在路由层表现为 404） |

## 未做 / 禁止宣称

- **未**做前端接线 / UI 冒烟；Motor：FE 接线后再 UI 闭环。
- **未**重建 `mo-api` 镜像；compose curl 不以本 tip 为准。
- **未**宣称 FEM **≤3%** / 解析 **≤5%**；未勾校准达标。
- **未**标 Q3-L4「已消化」全文：仅 **mems/artifacts API** 段 API 侧通过；live 几何包、AF Wasm、磁静力学 FEM 仍后置。

## 跟踪变更建议（本轮已落）

| 项 | 变更 |
| --- | --- |
| Q3-L4 / Q4 遗留 Q3-L4 | **部分消化（API）**：**API 侧通过（待 FE 接线）**；证据本文件；**不**标整行已消化 |
| Q4 产品项 | 本轮不改 P01–P11 状态 |

## 结论

| 项 | 结论 |
| --- | --- |
| tip `9ca055a` artifacts API | **PASS**（pytest 3/3 + TestClient list/GET/404/`manifest_not_found`/401） |
| compose 实 curl | **SKIP / 镜像落后**（记录在案；不否决） |
| L4 建议口径 | **API 侧通过（待 FE 接线）** / L4 **部分消化**；artifacts API 待产品确认与 FE 闭环后再谈整段关闭 |
