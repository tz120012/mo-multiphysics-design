# Q7-3 同壳后处理 — FEM 协作草案

| 项 | 值 |
| --- | --- |
| 状态 | **协作草案**（配合 Mo-前端同壳入口；**零新 API**） |
| 日期 | 2026-10-29（Asia/Shanghai） |
| Owner | Mo-有限元（契约诚实 / artifacts 形状）；同壳 UI = Mo-前端 |
| 开闸 | [Q7-开闸-Motor签字](../qa/Q7-开闸-Motor签字.md) tip **`30a37a7`** |
| 冻结 | [Q7-范围冻结](../qa/Q7-范围冻结.md) §B IN#3 / §B.1 / §D **Q7-C3** |
| 跟踪 | [Q7-验收跟踪](../qa/Q7-验收跟踪.md) **Q7-3** |
| 既有 | [Q3-F1](./Q3-F1-结果精简.md)、[Q4+-3](./Q4+-3-mems单文件与artifacts收口.md)、[Q5-2](./Q5-2-真磁静力学后处理.md)、[Q6-FEM-改参再触发](./Q6-FEM-改参再触发.md) |

> **硬口径**：同壳后处理 = Workspace 读 UEM 指针 → **既有** `GET /jobs/{id}/artifacts`（+ 单文件）；**≠** 新 REST；**≠** 改 mems/files 作 `/field` 主路径；**≠** MS 整机关闭；**禁勾**精度；heat-proxy **≠** 磁静力学；**不扩** F1/F2；**不改** Elmer/SIF 核心。

---

## 0. 摸底结论（本 tip · 零代码优先）

| 结论 | 依据 |
| --- | --- |
| **artifacts 契约已够 FE 同壳消费** | `GET /api/v1/jobs/{id}/artifacts` → `{ jobId, resultRef, artifacts[] }`；`GET .../artifacts/{path}` 拉精简件（`apps/api/app/routers/jobs.py`；Q4+-3 Motor F5=A） |
| **thinning scalars 同壳可读字段已诚实** | `packages/solver-fem/thinning.py`：`equationMode`（有则写入 manifest.scalars + scalars.json）、`dryRun`、`pending_calibration`（恒 true）、三件套 roles `scalars` / `slice` / `preview`；MS 路径另可有 `magnetostaticPathReady` / `postprocess` |
| **指针路径已约定** | Q6：UEM / 会话只存 `lastFemJobId` / `resultRef`；`/field` 主路径认 job-artifacts（禁静默复用旧 job） |
| **FE 已有降级骨架** | `FieldVizView.vue`：`job-artifacts` / `job-fixture` / `fixture`；`fieldPostprocess.ts` 读 `equationMode`；WorkbenchInspector 有 `lastFemJobId` 提示 |
| **本 tip 策略** | **不改** thinning / run_job / jobs 路由 / mems/files；仅协作文档 + 可选 dry-run 契约 smoke |

**同壳可读关键字段一览（已有 → 勿再改代码）：**

| 字段 | 出现位置 | 同壳用途 |
| --- | --- | --- |
| `equationMode` | `manifest.scalars` / `scalars.json` / job 回声 | 区分 heat_proxy vs magnetostatic；驱动降级文案 |
| `dryRun` | 同上 | dry-run ≠ 真 Elmer；文案须明示 |
| `pending_calibration` | 同上（恒 `true`） | **禁勾**精度 / ≤3% |
| `artifacts[].role` | manifest | `scalars` / `slice` / `preview` 三件套 |
| `resultRef` | Job + artifacts list | 指向 `solver/fem/jobs/{jobId}/manifest.json` |
| `magnetostaticPathReady` / `postprocess` | MS 路径可选 | 有限 MS 边界；**不可外推**整机 |

---

## 1. IN（同壳后处理）

```text
Workspace（C2 单壳）
  → 读 UEM / 会话：lastFemJobId（或 resultRef）
  → 既有 GET /api/v1/jobs/{id}/artifacts
  → 按 artifacts[].path 拉 scalars / slice / preview
  → 同壳展示标量摘要 + 预览/切片（可内嵌或链既有 /field?jobId=）
  → 与 Q6「改参→显式新 job」衔接：仅当改参后再求解、指针更新为新 jobId 后，才可标「结果已更新」
```

### 1.1 与 Q6 改参再触发的衔接（强制）

1. 改参后须 **新** `POST /jobs`（新 `jobId` / 新 `resultRef`），见 [Q6-FEM-改参再触发](./Q6-FEM-改参再触发.md)。  
2. 同壳后处理入口须绑定 **当前** `lastFemJobId`；标脏期间 **禁止**把旧场图标成「当前参数结果」。  
3. 「结果已更新」判定 = 再求解 succeeded **且** 会话指针已切到新 job（非仅 UI 刷新旧 artifacts）。  
4. `/field` 与同壳内嵌 **同一** artifacts 权威源；UEM **不**内嵌全量场文件。

### 1.2 消费顺序（FE）

1. 有 `lastFemJobId` → `GET /jobs/{id}`（状态）→ succeeded 则 `GET /jobs/{id}/artifacts`。  
2. list 非空 → 按 role/path `GET .../artifacts/{path}`（manifest 亦可经 resultRef 解析）。  
3. 用 `manifest.scalars` 或 `scalars.json` 展示 `equationMode` / `dryRun` / `pending_calibration`。  
4. 无 jobId / list 空 / 关键 GET 失败 → 走 §2 降级明示（保留 fixture，**禁止删除**）。

---

## 2. 降级明示表（UI 文案要求 · FE 主责）

| 情形 | 建议 source / 标记 | UI 文案要求（须用户可见，勿仅 console） | 禁止 |
| --- | --- | --- | --- |
| **无 jobId** | `fixture` | 「未绑定 FEM job；当前为 public fixture / 演示数据。不宣称误差达标。」 | 冒充本工程求解结果 |
| **显式 `?source=fixture`** | `fixture` 或 `job-fixture` | 「显式强制 fixture。不是该 job 精简产物。」 | 藏起来当 live |
| **有 jobId 但 artifacts 空/404** | `job-fixture` | 「已降级 public fixture（artifacts 不可达）。当前场数据 **不是** 该 job 精简产物。」 | 页眉仍写 job-artifacts |
| **`equationMode=heat_proxy`**（或缺省按兼容旧路径） | 可与 `job-artifacts` 并存 | 「heat-proxy / 热方程调度路径，**不是**磁静力学真值。校准未关闭。」 | **把 heat-proxy 当 MS**；勾 MS 整机关闭 |
| **`equationMode=magnetostatic`** | `job-artifacts` + MS 标记 | 「磁静力学路径（有限边界）；`pending_calibration` — **不宣称**整机 ≤3%/≤5%；F2 不可外推。」 | 外推 F1/F2；勾精度；宣称 MS 整机关闭 |
| **`dryRun=true`** | 任意 | 「dry-run：未调 Elmer；仅契约/调度。」 | 当真场验收 |
| **fixture 几何/样例** | — | 与后处理无关时仍禁「建模完成」 | fixture ≠ 建模完成（Q7 红线） |

**总禁（验收红线，对齐冻结 §D Q7-C3 / 跟踪）：**

- **禁**把 heat-proxy 当磁静力学。  
- **禁勾**精度（整机 ≤5% / ≤3%）。  
- **禁勾**「磁静力学整机关闭」。  
- **禁**默认新开 API；**禁**改 mems/files 作后处理主路径。

---

## 3. OUT（本阶段不做）

| OUT | 说明 |
| --- | --- |
| **零新 API** | 不新增 REST；不扩 OpenAPI 资源；复用 jobs(+artifacts) |
| 不改 mems/files 作 `/field` 主路径 | Q5-1 / Q4+-3 F5=A；`GET .../mems/files` 仍后置 |
| 不扩 F1/F2 | 有限边界不变；不可外推整机精度 |
| 不改核心求解 | 不改 Elmer/SIF / WhitneyAV / HeatEquation 物理 |
| 不重开 MVP / v1.0.0 / Q5 | 仅体感同壳入口 |
| 不把同壳做成第二套场协议 | 与 `/field` 共用 artifacts 形状 |

---

## 4. 与 FE / 测试分工

| 角色 | 职责 |
| --- | --- |
| **Mo-前端** | Workspace **同壳入口**（读 `lastFemJobId`/`resultRef` → artifacts）；§2 **明示文案**；改参标脏；指针更新后才「结果已更新」；可复用 `FieldVizView` / `fieldPostprocess` |
| **Mo-有限元** | **保证** manifest/scalars 字段诚实（本 tip：已有则只文档引用）；可选 dry-run 契约 smoke；**不**改求解核心 |
| **Mo-后端** | 稳住既有 artifacts list/get（共享卷 / 嵌入 manifest）；**不**为本项新开端点 |
| **Mo-测试** | 冒烟 **Q7-C3**（见 §5）；未测过不得放行 |

---

## 5. 给测试的 Q7-C3 勾选提示（可测点）

对齐冻结 §D：**后处理同壳；降级明示；禁勾精度/MS 整机**。

| # | 可测点 | 期望 | 不通过信号 |
| --- | --- | --- | --- |
| C3-1 | 同工程 Workspace 可见结果/场量入口 | 有 `lastFemJobId`（或等价）时可打开同壳后处理 / `/field?jobId=` | 只能跳到无关页且无指针 |
| C3-2 | 主路径 | 带真实 jobId 且产物可达 → `source=job-artifacts`（或同壳等价标记） | 有产物仍强制 fixture 且不说明 |
| C3-3 | 改参→再求解→指针 | 新 jobId；旧 artifacts **不得**标「结果已更新」 | 静默复用旧 jobId |
| C3-4 | 无 jobId / fixture | 明示「fixture / 未绑定 job」类文案 | 无文案冒充本工程结果 |
| C3-5 | job-fixture | 有 jobId 但 artifacts 失败 → 明示「不是该 job 精简产物」 | 页眉写 live/job-artifacts |
| C3-6 | heat_proxy | 文案含「不是磁静力学」或等价；**未**勾 MS 整机关闭 | heat-proxy 当 MS |
| C3-7 | magnetostatic（若测） | 可见 MS 路径标记 + `pending_calibration`；**未**勾精度 / 整机关闭 | 勾 ≤3% 或「MS 整机完成」 |
| C3-8 | 契约边界 | 网络/文档无新后处理 REST；未改 mems/files 主路径 | 出现新 `/field-post/*` 等 |

**文档级 FEM 复现（无 Elmer，可选）：**

```bash
python3 packages/solver-fem/smoke/run_q7_shell_postprocess_contract.py
# 亦可对照 Q6：python3 packages/solver-fem/smoke/run_q6_retrigger_smoke.py
```

期望：两次 dry-run 后 manifest 含诚实 `equationMode`；`resultRef` → manifest；`artifacts[]` 含 scalars/slice/preview 形状（供 FE 同壳消费断言）。

---

## 6. 交付物

| 交付 | 路径 |
| --- | --- |
| 本文 | `docs/drafts/Q7-3-同壳后处理-FEM协作.md` |
| 契约 smoke（可选） | `packages/solver-fem/smoke/run_q7_shell_postprocess_contract.py` |
| 索引 | [docs/drafts/README.md](./README.md) |

**代码策略**：**零** thinning / jobs / mems/files / Elmer 改动；同壳 UI 归 FE。

---

## 修订记录

| 日期 | 说明 |
| --- | --- |
| 2026-10-29 | 初稿：摸底确认既有 artifacts + scalars 足够；钉 IN/降级表/OUT/分工/Q7-C3 可测点；开闸 tip `30a37a7` |

---

*Mo-有限元 · Q7-3 · 开闸 `30a37a7` · **零新 API** · 隔离仅 `/workspace/mo-platform`*
