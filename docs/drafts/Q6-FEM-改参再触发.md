# Q6 FEM：改参 → 再触发（协作草案）

| 项 | 值 |
| --- | --- |
| 状态 | **协作草案**（配合 Q6 闭环；不扩 F2、不改求解核心） |
| 日期 | 2026-10-29（Asia/Shanghai） |
| Owner | Mo-有限元 |
| 开闸 | [Q6-开闸-Motor签字](../qa/Q6-开闸-Motor签字.md) tip **`cc3b2d1`** |
| 架构 | [Maxwell-first统一工程模型与实时视口](./Maxwell-first统一工程模型与实时视口.md) tip **`6dafa91`**；分叉 [A1+B1+C2+D1](../qa/Q6-架构分叉-Motor拍板.md) tip **`be6ed88`** |
| 对照 | [Q4plus-5](./Q4plus-5-磁静力学与轴向真值.md)、[Q5-2](./Q5-2-真磁静力学后处理.md)、[FEM范围](./FEM范围.md)、[Q6-验收跟踪](../qa/Q6-验收跟踪.md) Q6-3 |

> **硬口径**：`heat-proxy` ≠ 磁静力学；**不扩大** F1/F2；**不改** Elmer/SIF 核心算法；FEM **显式提交**（禁拖拽/滑条与 FEM 耦合）；`/field` 仍走 job-artifacts。

---

## 0. 摸底结论（本 tip）

| 结论 | 依据 |
| --- | --- |
| **`POST /jobs` `jobType=fem` 已可重复提交** | 每次 `job_create` 新 `uuid4` → 新 `jobId` → 新 `resultRef=solver/fem/jobs/{jobId}/manifest.json`（`apps/api/app/jobs_store.py` / `tasks/fem.py`） |
| **求解入口不变** | `packages/solver-fem/run_job.py`：`resolve_template` / `resolve_equation_mode` / `run_job`；Celery `app.tasks.fem.run_fem_job` 透传 payload |
| **payload 契约已够** | `packages/solver-fem/api/fem-job-payload.schema.json` + `FemJobPayload`（`apps/api`）；必填：topology / machineType / dim / solverKernel / meshProfile / operatingPoint / materials；可选 `templateId` / `equationMode` / `dryRun` |
| **组装属 FE/API** | 架构 P2：从 UEM 组 `jobType=fem`；**solver-fem 保持入口不变**，本 tip **不**新增 `assemble_payload` 到求解包 |

---

## 1. IN（闭环）

```text
UEM（或等价会话切片：geometry / materials / OP / femEntryHint）
    → FE/API 组装既有 FemJobPayload
    → 用户显式「求解 / 再求解」→ POST /jobs { jobType: fem, payload }
    → Celery fem 队列 / in-process degrade → run_job
    → artifacts（manifest + thinning）
    → /field 主路径 GET /jobs/{id}/artifacts（UEM 只存 lastFemJobId / resultRef 指针）
```

### 1.1 改参再触发规则

1. **每次改参后的 FEM 求解须新 job**（新 `jobId` / 新 `resultRef`），或会话显式标脏后再 submit。  
2. **禁止**静默复用旧 artifacts / 旧 `jobId` 冒充「已随参数更新」。  
3. 视口参数 debounce **只**驱动几何 rebuild（A1+D1）；**不得**自动 enqueue FEM。  
4. 结果回填：轮询 `GET /jobs/{id}` → succeeded 后把 `resultRef` / 精简标量投影进 UEM 结果切片；`/field` 仍认 artifacts。

### 1.2 字段映射建议（UEM → FemJobPayload）

| UEM / 会话切片 | FemJobPayload 字段 | 说明 |
| --- | --- | --- |
| geometry（topology / machineType / dim） | `topology` / `machineType` / `dim` | 与 mems `geometry/params`、pipeline `femEntryHint` 对齐 |
| geometry / mesh 策略 | `meshProfile` | 如 `rf_pmsm_2d_default` / `af_pmsm_3d_min` / `af_pmsm_3d_ms_min` |
| materials | `materials` | object 或 array；与 Q2 materials / mems `materials/` 一致 |
| operatingPoint / excitation | `operatingPoint` | 工况切片；自由 object |
| `femEntryHint` / 用户选模板 | `templateId` | 见下表暗示规则 |
| 求解意图 | `equationMode` | `heat_proxy` \| `magnetostatic`；**诚实标注** |
| （可选） | `dryRun` | 仅调试；工人闸门仍以 `MO_FEM_DRY_RUN` 为准 |
| （可选） | `projectId` | 回声校验 |
| （固定） | `solverKernel` | MVP：`elmer`（GetDP 磁静力学未接线） |

**`templateId` → `equationMode` 暗示（组装侧须写清）：**

| templateId | 建议 equationMode | 备注 |
| --- | --- | --- |
| `af_pmsm_3d_ms` | **`magnetostatic`** | `run_job.resolve_equation_mode`：缺省 `equationMode` 时已暗示 magnetostatic |
| `ms_gap_force_3d` | **`magnetostatic`** | 闭磁路验证案（有限 F2）；**组装侧须显式写** `equationMode=magnetostatic`（runner 当前仅对 `af_pmsm_3d_ms` 自动暗示） |
| `rf_pmsm_2d` / `af_pmsm_3d` | `heat_proxy`（或省略） | HeatEquation E2E；**≠** 电机磁解 |
| 省略 + `dryRun=false` | 兼容 **`heat_proxy`** | 不得默认为磁静力学 |

---

## 2. OUT（本阶段不做）

| OUT | 说明 |
| --- | --- |
| 不改 Elmer / SIF 核心算法 | 不改 `case.sif` 物理、不重写 WhitneyAV / HeatEquation |
| 不扩大 F2 | F2 有限仅 `ms-gap-force-001` / `ms_gap_force_3d` / body-rms；不可外推整机 / `af_pmsm_3d_ms` |
| 不把 heat-proxy 当磁静力学 | UI / notes / scalars 须诚实；禁用温度场冒充 `axialForceN` |
| 不绑视口实时 FEM | 禁拖拽/滑条耦合 FEM；FEM 仅显式按钮/菜单 |
| 不重开 MVP / v1.0.0 / Q5 | 配合闭环即可 |
| 不把 `/field` 改成 mems/files 主路径 | Q5-1 已锁定 |

---

## 3. 与 FE / 后端协作点（一句话）

| 角色 | 职责 |
| --- | --- |
| **Mo-前端（UEM）** | **组装** FemJobPayload（读 UEM geometry/materials/OP/`femEntryHint`），用户显式点击后 `POST /jobs`；会话存 `lastFemJobId`/`resultRef`；标脏后禁止展示旧场图为「当前参数结果」。 |
| **Mo-后端** | **校验** `FemJobPayload` → **enqueue** `run_fem_job`（或 degrade 同进程）；轮询与 artifacts API；**不**在 API 进程内嵌 Elmer。 |
| **Mo-有限元** | **保持** `run_job` / thinning / 模板入口；本 tip 只提供协作口径 + dry-run 再触发冒烟；真解仍走既有 magnetostatic / heat-proxy 分界。 |

---

## 4. 冒烟建议

### 4.1 文档级复现（无 Elmer，推荐）

```bash
# 同一「参数」改两次，各 dry-run submit 一次 → 两个 jobId/resultRef 不同，equationMode 诚实
python3 packages/solver-fem/smoke/run_q6_retrigger_smoke.py
```

期望 stdout JSON：

- `pass: true`
- 两次 `jobId` / `resultRef` **互不相同**
- 第一次 `equationMode=heat_proxy`；第二次（改参 + `templateId=af_pmsm_3d_ms`）`equationMode=magnetostatic`
- 两侧均 `pending_calibration` 口径保留（magnetostatic 路径）

### 4.2 API 级（compose 起来时）

```bash
# 同一 projectId 连续两次 POST jobType=fem（payload 改 operatingPoint 或 templateId）
# 断言：两次 jobId 不同；GET /jobs/{id}/artifacts 各自独立；禁止把第一次 artifacts 当第二次结果
```

### 4.3 真 Elmer（可选，非本 tip 必达）

沿用 [Q5-2](./Q5-2-真磁静力学后处理.md)：`smoke/run_magnetostatic_truepath.py`；**仍** `pending_calibration`（除有限 F2 验证案书面范围外禁宣称 ≤3%）。

---

## 5. 交付物

| 交付 | 路径 |
| --- | --- |
| 本文 | `docs/drafts/Q6-FEM-改参再触发.md` |
| 再触发 smoke | `packages/solver-fem/smoke/run_q6_retrigger_smoke.py` |
| 索引 | [docs/drafts/README.md](./README.md) |

**代码策略**：不新增 solver-fem 组装器；不改 `run_job` 求解核心；组装在 FE/API。

---

*Mo-有限元 · Q6 改参再触发；heat-proxy ≠ MS；不扩 F2；主会话回报 Motor。*
