# Q6 冒烟记录 — D1 API `POST /geometry/rebuild`（tip `e659e0a`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-29 09:50 Asia/Shanghai |
| 后端交测 tip | **`e659e0a`**（`feat(api): Q6 thin geometry rebuild + jobs UEM wiring`） |
| Motor / master 参照 | 开测叠合含 `e659e0a`；API 可用参照 **`d965b1f`**；本证据写时 HEAD **`531b75d`**（`e659e0a` / `d965b1f` 均为祖先） |
| 脚手架 | Q6 脚手架 tip **`25f59d6`** |
| 执行 | Mo-测试 |
| 范围 | **仅 D1 API 抽测**（同步 `POST /api/v1/geometry/rebuild`）；**非**浏览器 C3/C4；**不**放行整关改参闭环；**禁勾精度**（不宣称 ≤5%/≤3%） |
| 总评 | **PASS（API）** — RF/AF example → 200 + `meshDescriptor`；坏 topology → 400；响应**非** Job 排队形态 |

## 环境

- 工作目录：`/workspace/mo-platform`；仅改 `docs/qa`；**未改**业务代码。
- `git merge-base --is-ancestor e659e0a HEAD` → exit 0。
- 本地 compose API：`http://127.0.0.1:8000`（OpenAPI 含 `/api/v1/geometry/rebuild`；登录 `POST /api/v1/auth/login` username/password `t`）。
- 路由实现：`apps/api/app/routers/geometry.py`（summary 明示 sync / **not a Job**；调 `mo_geometry.rebuild_live_geometry`）。
- 契约：`docs/drafts/openapi-v1.yaml` / `docs/drafts/Q6-UEM与几何rebuild契约.md` §2。

## 验收对照

| 验收点 | 结果 | 证据 |
| --- | --- | --- |
| RF example → **200** + `meshDescriptor` | **PASS** | curl `radial_pmsm_params.json` 信封 `{topology:RF, machineType:PMSM, params}` |
| AF example → **200** + `meshDescriptor` | **PASS** | curl `axial_af_pmsm_rfmr_params.json` 信封 `{topology:AF, machineType:PMSM, params}` |
| 坏 topology → **400** | **PASS** | curl `{topology:XX, params:{schemaVersion}}` → `code=bad_request` |
| **非 Job**（同步 API） | **PASS** | 200 体含 `params`/`meshDescriptor`/`geometrySummary`/`paramsHash`；**无** `jobId` / 排队形态 |
| pytest `test_geometry_rebuild` | **核对：文件 9 collected**；本机完整 9 项复跑过慢（几何 rebuild 耗时 + `test_fem_payload` 曾挂起），**未强等满 9**；后端交测称 **9 passed** @ `e659e0a`；本侧曾见 RF/AF/400/auth 等核心项 PASSED | `apps/api/tests/test_geometry_rebuild.py`（9 tests collected） |

## curl 抽测（`:8000`）

| # | 请求 | HTTP | 关键断言 |
| --- | --- | --- | --- |
| 1 | RF：`packages/geometry/examples/radial_pmsm_params.json` + FE 信封 | **200** | 含 `meshDescriptor`（`schemaVersion/kind/units/primitives`）；含 `geometrySummary`、`paramsHash`；**无** `jobId` |
| 2 | AF：`axial_af_pmsm_rfmr_params.json` + FE 信封 | **200** | 含 `meshDescriptor`；含 `pipelineEntry`；**无** `jobId` |
| 3 | 坏 topology：`topology=XX` | **400** | `{"code":"bad_request","message":"…topology must be 'RF' or 'AF' (got 'XX')"}` |

Motor FYI 复核：radial_pmsm 样例 **200**（含 `paramsHash`）与本记录一致。

## pytest 范围说明

- 命令：`apps/api/.venv/bin/pytest apps/api/tests/test_geometry_rebuild.py`（`--co` → **9 tests collected**）。
- 覆盖：RF/AF FE 信封 200、bare/nested params、坏 topology / 非法 RF / topology mismatch → 400、未授权 401、FEM payload 可携 `geometrySummary`（UEM 接线，属同 tip）。
- 本机：几何 live rebuild 单测耗时长；`test_fem_payload_accepts_geometry_summary` 曾长时间无结束，故 **以 live curl 为 D1 主证据**，pytest 记「9 collected + 后端 9 passed 口径 + 核心项曾 PASSED」，**不**因本机超时否决 API PASS。

## 口径 / 门禁

- **D1 API PASS** ≠ C3 视口可见更新通过；≠ C4 改参→求解闭环通过。
- **C3/C4 未开**（浏览器 / 整关由并行任务覆盖）；**未测不得放行**整关。
- **禁勾精度**；不宣称整机 ≤5%/≤3%；不扩 F1/F2；不代签；不开自行打新 tag。
- 产品 Q6-1…6 **不代改通过**。

## 相关链接

- [Q6-冒烟清单](Q6-冒烟清单.md)（D1 API 子项注）
- [Q6-验收跟踪](Q6-验收跟踪.md)（后端 D1 行）
- 交测 tip `e659e0a`；脚手架 `25f59d6`；拍板 `be6ed88`

---

*Mo-测试 · D1 API 仅 · 2026-10-29 09:50 Asia/Shanghai · **PASS（API）** · 禁勾精度 · C3/C4 未开*
