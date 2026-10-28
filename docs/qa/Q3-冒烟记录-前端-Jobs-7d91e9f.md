# Q3 冒烟记录 — 前端 tip `7d91e9f`（P02/P06 Jobs 真接线）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:16 Asia/Shanghai |
| 指派 tip | **`7d91e9f`**（`feat(web): wire FEM Jobs submit+poll on axial and field by resultRef`） |
| 配合核对 | P07 骨架 tip **`8ce8944`**（Motor 正式确认跟踪 **`c4ef3b7`**） |
| 仓库 HEAD（入库时） | 本证据 tip（`7d91e9f` / `8ce8944` 均为祖先） |
| 执行 | Mo-测试执行员（API curl 自证 + **浏览器实测结论照抄入库**） |
| 范围 | `/axial` 提交 FEM + poll + resultRef；`/field` 按 jobId/resultRef；L3 金标重拷抽查；P07 骨架核对 |
| Jobs 提交链总评 | **PASS**（dry-run succeeded + resultRef；真 Elmer 非必须） |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `git merge-base --is-ancestor 7d91e9f HEAD` → 0；`8ce8944` → 0 |
| UI BASE_URL | **`http://127.0.0.1:5173`**（`pnpm`/vite dev；`vite.config` proxy `/api`→`:8000`） |
| 为何非 5174 | compose `mo-web:5174` nginx→`host.docker.internal:8000` **超时**（Pingora 500 / box 代理挂起）；本轮 UI **规避**走 vite:5173 |
| 静态对照 | compose:5174 曾 docker cp `apps/web/dist`（`index-FAOo7eID.js`；Axial chunk 含「提交 FEM」）；**不以 5174 作本轮浏览器结论** |
| API | `:8000`；`GET /health` → status=ok；db/redis ok |
| 鉴权 | `POST /api/v1/auth/login` `demo/demo` → Bearer |
| FEM | `MO_FEM_DRY_RUN=1`；worker 在跑；dry-run succeeded + resultRef 即 Jobs 链 PASS |
| 未改 | **未**改 `apps/` 业务代码；本记录仅 `docs/qa/` |

环境备忘：`/tmp/mo-q3-fe-smoke-env.txt`（BASE_URL=5173）。

## API 抽测（curl :8000）

| 步骤 | 结果 | 判定 |
| --- | --- | --- |
| login demo | accessToken 签发 | PASS |
| projectId | `ad78eb71-e5a7-42b4-bcca-0388b93fa32d`（既有工程） | PASS |
| POST `/api/v1/jobs` `jobType=fem`（AF/PMSM/3d） | **202** → job `bb9a6699-d8b9-494e-b75b-56792df85400` | PASS |
| GET `/jobs/{id}` | **succeeded**；`resultRef=solver/fem/jobs/bb9a6699-…/manifest.json` | PASS |
| manifest | `scalars.dryRun=true`；`pending_calibration=true`；notes=API stub | PASS（dry-run） |
| 前端形 payload（`meshProfile=af_pmsm_3d_min`） | job `474b40da-4174-4988-9bf6-612bbaf71da7` → **succeeded** + resultRef | PASS |

> 无 mems 单文件 GET（已知缺口）→ **不否决** Jobs 提交链。

## 浏览器实测（照抄；vite:5173）

### /axial — Jobs submit+poll+resultRef：**PASS**

| 项 | 实测 |
| --- | --- |
| 登录 | demo/demo → `/projects` → `/axial` |
| 按钮 | 「提交 FEM」「查看场量」「仅打开 dry-run 场量样例」可见 |
| 提交 FEM | toast `FEM 已提交 · queued` → `FEM 成功`；pill **SUCCEEDED** |
| jobId | **`913d2d89-614d-43f6-943a-0a32adc4ec57`** |
| resultRef | **`solver/fem/jobs/913d2d89-614d-43f6-943a-0a32adc4ec57/manifest.json`** |

### /field — job 打开 + fixture 降级：**PASS**（不否决）

| 项 | 实测 |
| --- | --- |
| 路由 | `/field?jobId=…&resultRef=…`（自「查看场量」） |
| 降级 | **yes**：`source=job-fixture`；警告「无 mems 单文件 GET；…产物降级 fixture」 |
| 判定 | 已知缺口；**不否决** Jobs 链 |
| 截图 | `/workspace/mo-fem-smoke/field-job-fixture.png`（未强制 git add） |

### 可选 dry-run 样例 — **PASS**

| 项 | 实测 |
| --- | --- |
| 入口 | 「仅打开 dry-run 场量样例」→ `source=fixture` |
| 截图 | `/workspace/mo-fem-smoke/field-dryrun-sample.png` |

## L3 金标重拷（同 tip）

| 文件 | 与 tip `7d91e9f` |
| --- | --- |
| `apps/web/public/solver/axial_pmsm_request.json` | **MATCH** |
| `apps/web/public/solver/axial_pmsm_result.json` | **MATCH** |

一句话：本 tip 含 L3 金标重拷；工作树与 tip blob 一致。

## P07 核对（`8ce8944` / Motor `c4ef3b7`）

| 项 | 结论 |
| --- | --- |
| Q3-F1 / F2 / F3 | **骨架 PASS**（已落；本轮复核无漂移） |
| Q3-A5 | **骨架 PASS**（交叉 `5c0320e`） |
| Motor | 正式确认跟踪 **`c4ef3b7`**：**P07 骨架通过、仍进行中** |
| 校准 / 数值 | **本轮不开**；**未**勾 F4/F5；**未**宣称 ≤3%/≤5% |
| 代签 / Q4 | **未**代签；**未**开 Q4 |

## 已知缺口（不否决 Jobs 链）

- 无 mems 单文件 GET → 场量产物降级 F1 dryrun fixture（本轮已见）
- compose:5174 nginx→host.docker.internal 代理超时（环境；UI 改走 vite:5173）
- live 几何包 / AF Wasm / 磁静力学 FEM / 真场可视化
- 校准与误差达标书面关闭前 **禁止** 宣称 ≤5%/≤3%

## 未做 / 禁止宣称

- **未**勾选或宣称解析相对标杆 **≤5%** / FEM **≤3%**。
- **未**以 Jobs dry-run PASS 冒充真 Elmer / 磁静力学 / 误差达标。
- **未**代签；**未**开 Q4。
- **未**改 `apps/`；本记录仅文档。

## 跟踪变更（测试建议 / 按惯例可更新状态）

| 项 | 变更 |
| --- | --- |
| Q3-P02 | **通过（几何）+ 通过（前端壳）+ 通过（Jobs 接线）**（tip `7d91e9f`；证据本记录；建议产品确认） |
| Q3-P06 | **通过（dry-run 壳）+ 通过（Jobs 接线）**（`/field` resultRef + fixture 降级不崩；建议产品确认） |
| Q3-P07 | **维持进行中（骨架通过）**；Jobs UI 冒烟本轮已关；仍等签字包；校准不开 |
| Q3-L4 | Jobs 真接线本轮测通 → 备注可收；余 live 几何 / AF Wasm / 磁静力学 |

## 结论

| 项 | 结论 |
| --- | --- |
| Jobs 提交链（API+UI） | **PASS** |
| /axial submit+poll+resultRef | **PASS** |
| /field jobId/resultRef + fixture 降级 | **PASS**（缺口不否决） |
| L3 金标重拷 | **MATCH** tip `7d91e9f` |
| P07 骨架核对 | **PASS**（`8ce8944` / `c4ef3b7`） |
| ≤3% / ≤5% | **未宣称**（禁止） |
