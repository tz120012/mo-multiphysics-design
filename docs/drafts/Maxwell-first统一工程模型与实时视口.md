# Maxwell-first：统一工程模型与实时视口（路径建议）

| 字段 | 内容 |
| --- | --- |
| 维护 | Mo-架构 |
| 日期 | 2026-10-29 Asia/Shanghai |
| 状态 | 架构建议稿（待 Motor 拍板分叉） |
| 依据 | Motor·用户硬口径 **Maxwell-first（教学后置）**；开闸/基线 tip 自查：`b71b355`（FE 钉 `1.0.0`）、`8d9fc3b` / `4b553f5`（Q5-1/Q5-5）、`d054fb5`（产品确认 Q5-1/Q5-5）、几何 live `docs/drafts/几何-Q4plus-live与降级.md`、`mems-schema-v1.md`、`Q5-1-mems-files边界.md`、`Q2-材料与解析边界.md` |
| 仓库 | 仅 `/workspace/mo-platform` |
| 约束 | **不改** `docs/01`、`docs/02` 正文；禁宣称 MVP；禁勾 ≤5%/≤3%；Web / Three.js **可保留**；重大分叉报 Motor |

> 本文是**架构路径建议**，不是实现承诺、不是误差门禁、不是 MVP 声明。  
> 教学/向导 UI **后置**（可保留路由），主路径对齐商用 Maxwell 链：几何→材料→激励→网格→求解→后处理。

---

## 0. 现状（对照静态 fixture）

### 0.1 Workspace 现今数据源

| 面 | 事实（tip 自查时） |
| --- | --- |
| `/workspace` | **主读静态 fixture**：`public/mesh/{radial_pmsm,radial_acim,axial_af_pmsm_rfmr}_{mesh,params}.json`。`projectId` 仅 query 展示，**不**拉 `.mems` / mems/files。 |
| 参数面板 | ACIM 导条等为**本地占位**：注释写明「改字段仅更新本地 params 显示」，**不重算 mesh**；变更进 `history` 命令栈（`geometry.params.set`），但 Three 仍吃旧 `MeshDescriptor`。 |
| Three.js 视口 | `Viewport3D` ← `meshDescriptorToGroup`；descriptor 变则整组替换。栈保留（Vue3 + Three）。 |
| `/analytic` | 独立表单，默认 `DEFAULT_RADIAL_*_REQUEST`；材料可选 `GET /materials`；`projectId` 多为标签。**不**订阅 Workspace mesh/params。 |
| `/axial` | AF 工作流独立；求解降级序 sync→fixture（禁 Wasm AF）。几何入口可吃 public `geometry/*pipeline_entry`，与 Workspace 样例**平行**。 |
| `/field` | **主路径 job-artifacts**（`GET /jobs/{id}/artifacts`）；无 `jobId` / 显式 `?source=fixture` / 列表空失败 → public FEM dry-run fixture。**明确不走** mems 整包与 mems/files（Q4+-3 / Q5-1 边界）。 |
| `/drive`·`/compare` | Jobs `jobType=drive` 或 public `/drive/*_sample.json`；与 Workspace 几何无共享会话。 |
| 后端几何 | `packages/geometry` 已有 Python live：`rebuild_live_geometry` / `build_*_mesh_descriptor` / `export_geometry_summary`。**无**面向浏览器的稳定「参数→mesh」HTTP 主路径；FE 仍靠静态拷贝。 |
| Pinia | 仅 `auth` / `projects`（列表元数据）/ `history`（Workspace 本地栈）。**无**跨页 `ProjectSession`。 |

### 0.2 参数改动 ↔ 几何重建 / Three 更新

- **否（现状）**：改 ACIM/几何相关本地字段 → 不触发 `rebuild_live_geometry`、不打后端、不换 mesh JSON → Three **不**随参数实时变形。
- 换「样例」radio → 重新 `fetch` 静态 mesh → 视口全量替换（样例级，非参数级）。
- analytic / FEM / drive **各读各的**默认或 query；多页断裂。

### 0.3 断裂点列表

1. **几何页**：Workspace 真相 = `public/mesh` fixture；`.mems` `geometry/params.json` / mems/files 未接入主路径。  
2. **材料**：材料库 API 在 Analytic 侧消费；Workspace ACIM `barMaterialId` 手填字符串，无统一材料切片。  
3. **解析**：Analytic 表单自带 `geometry`（SI snake）与 Workspace mesh/params（camel/mm）**双源**；改一边不改另一边。  
4. **FEM / 场图**：`/field` 只认 job-artifacts（正确按 Q5-1），但提交 FEM 的 geometry/材料/激励与 Workspace/UEM **无组装契约**；结果不回写到共享会话切片。  
5. **激励 / drive**：Drive payload 自建；与 mems `drive/`、解析工况、Workspace 无单一工程树。

---

## 1. 目标架构（Maxwell-first）

### 1.1 统一工程模型（UEM）

内存中单一 **`ProjectSession`**（名称可等价），绑定：

| 切片 | 内容 | 权威回写 |
| --- | --- | --- |
| 身份 | `projectId` + 打开中的 `.mems` 语义树投影 | `GET/PUT /projects/{id}/mems`；成员读 `GET .../mems/files/{path}` |
| geometry | `geometry/params.json` 语义（camel + 单位；`poleCount` 权威） | mems 成员 / 整包 |
| materials | 引用 id + 可选覆盖；解析前 `resolveMaterials` | materials API + mems `materials/` |
| excitation \| drive | 工况 / 电调定义 | mems `drive/` + Jobs drive payload |
| solver 输入 | 由 geometry→`GeometrySummary` + materials + OP 组装的 SolveRequest / FEM hint | 不另起几何真相 |
| 派生视图 | `meshDescriptor`、Three 场景句柄、analytic/FEM **结果切片**（只读投影） | Jobs artifacts / `solver/*` 回写后再投影 |

**原则：** 前端 UEM = **会话投影**；包 + OpenAPI 仍是持久权威。禁止第二套「页面私有几何真相」。

### 1.2 参数 → 实时视口

```text
参数面板写 UEM.geometry
    → debounce（建议 150–300ms）
    → 几何引擎（优先：现有参数化 → MeshDescriptor；可 WASM 加速图元；可薄封装后端 rebuild）
    → UEM.derived.meshDescriptor
    → Viewport3D 增量（同拓扑改尺寸）或全量替换（换机型/槽极）
```

- **默认前端本地**重建，目标**秒级**体感；**不**每键击打 FEM / analytic Jobs。  
- Three.js **保留**；继续 `meshToThree` / 现有 OrbitControls 路径。

### 1.3 analytic / FEM 与 UEM

- analytic **同步求解按钮**：从 UEM 导出 `GeometrySummary` + materials + OP → 现有 Wasm→sync→fixture 降级序（RF）；AF 仍 sync→fixture。  
- FEM：**显式提交**；payload 从 UEM 组装；结果经 Jobs artifacts → `/field` 主路径；可选把精简标量/refs 投影进 UEM 结果切片；持久成员走 mems（非 `/field` 替代）。  
- **禁止** analytic/FEM 页面另维护一套与 UEM 冲突的 geometry 源（可保留「高级覆盖」但须标脏并写回 UEM）。

### 1.4 教学后置

- 向导/逐步讲解路由**可保留**，不删文档、不删样例。  
- 主入口 = 工程 Workspace（Maxwell 链工具壳），教学为辅线。

---

## 2. 技术路径（分阶段，可落地）

栈衔接：**Vue3 + Pinia + Three.js + FastAPI + `packages/geometry`（Python live）+ `solver-analytic(-wasm)` + Jobs/Celery**。不重写整个前端。

### P0 — 去静态 fixture **主路径**；参数驱动视口

| 项 | 做法 |
| --- | --- |
| UEM 最小核 | 新建 `stores/projectSession.ts`（或等价）：`projectId`、`geometry.params`、`meshDescriptor`、`dirty` 标志 |
| 打开工程 | 有 `projectId`：优先 `mems/files/geometry/params.json`（Q5-1）；失败再整包 `getMems` 抽成员；再失败 → **保留**现有 public mesh fixture 降级 |
| 参数面板 | 写 UEM，不再「只改显示」；debounce 后调几何重建 |
| 几何重建 | **推荐默认（待 Motor 拍 F-A）**：P0 先走 **薄 API** `POST`（或已有内部）封装 `rebuild_live_geometry` / `build_*_mesh_descriptor`，返回 descriptor；并行评估把图元构建迁浏览器（TS 移植或 geometry Wasm）以降延迟 |
| Three | 订阅 `meshDescriptor`；同机型尺寸变更可先全量替换（实现简单），P1 再做增量 |
| fixture | **不删**：无网/无包/演示仍可 `?source=fixture` 或样例 radio |

**出口（建议）：** 改槽极/气隙/导条尺寸 → 视口可见更新；仍可一键降级静态样例。

### P1 — 材料 / 激励进 UEM；analytic 读 UEM；场图继续 artifacts

| 项 | 做法 |
| --- | --- |
| materials | Analytic 材料选择写入 UEM；`listMaterials`/`getMaterial` 复用；Workspace 显示同一 id |
| excitation | 工况 OP + 可选 drive 草稿进 UEM；Drive 页读同一切片再组 Jobs payload |
| analytic | 「求解」按钮：`UEM → SolveRequest`；结果进 UEM.results.analytic；快照形状沿用 `analyticSnapshot.ts`（PUT 仍显式） |
| `/field` | **不变主路径** job-artifacts；UEM 只存 `lastFemJobId` / resultRef 指针 |

### P2 — FEM 从 UEM 组装；mems 持久化

| 项 | 做法 |
| --- | --- |
| FEM submit | `femEntryHint` + geometry/materials/OP 从 UEM 组装 `jobType=fem` |
| 成员拉齐 | 需要包内其它文件时走 mems/files（非 field） |
| 持久化 | 显式「保存工程」→ 把 UEM 脏切片写回 `geometry/params` 等，再 `PUT mems`（或未来 member PUT；**本阶段非目标**强上 member 写） |
| 路由壳 | 见分叉 F-C：默认可先多路由 + 共享 UEM，再收单壳 |

---

## 3. 服务 / 契约边界

| 主题 | 钉法 |
| --- | --- |
| 权威 | `.mems` + OpenAPI；UEM = 会话投影，可丢可重建 |
| 实时视口 | **默认前端本地**（或薄 rebuild API）几何重建；**禁止**拖拽/滑条与 FEM 耦合 |
| analytic / FEM Jobs | **显式动作**（按钮 / 菜单）；可与「自动解析预览」开关分开，默认关 |
| `/field` | 继续 Jobs artifacts；**不要**改成 mems/files 主路径（Q5-1 已锁定） |
| 版本 | 整包 `memsSchemaVersion` 钉展示/写入 `1.0.0`；读双接受 `1.0.0` / `1.0.0-draft`（FE `b71b355`）；几何子 schema 仍 `0.1.0-q1` 双轨 |

### 复用一览

| 能力 | 复用点 | UEM 关系 |
| --- | --- | --- |
| mems/files | `GET .../mems/files/{path}` | 打开/补拉成员 → 填 UEM |
| GET/PUT mems | 整包 I/O | 会话加载 / 显式保存 |
| Jobs artifacts | `/field`、FEM/optimize 精简件 | 结果指针进 UEM；不替代几何真相 |
| materials API | `GET /materials` | UEM.materials 解析 |
| geometry 包 | `rebuild_live_geometry`、mesh descriptor、`GeometrySummary` | 视口 + analytic/FEM 输入唯一几何导出 |
| analytic Wasm/sync | 现有降级序 | 读 UEM，不读页面私货 |
| Three.js / meshToThree | 现有视口 | 订阅 UEM.derived.meshDescriptor |
| history 栈 | Q1-6 命令 | 命令改 UEM；undo 触发同路径重建 |

---

## 4. 重大分叉（报 Motor 拍板）

### F-A — 几何真相重建落点

| 选项 | 含义 |
| --- | --- |
| **A1（默认推荐）** | **浏览器本地**（TS 移植关键图元子集 **或** geometry Wasm）为主；后端 `rebuild_live_geometry` 作金标/降级/无 Wasm 时 |
| A2 | **始终**打后端几何服务（每参数变更 HTTP） |

**默认 A1 · 为何 Maxwell-first：** 参数拖动要**视口实时**；秒级体感不能绑 Celery/FEM。Python 包已是权威生成器——浏览器实现须与 `MeshDescriptor` / examples **对拍**，后端保留金标与无 Wasm 降级。

### F-B — UEM schema

| 选项 | 含义 |
| --- | --- |
| **B1（默认推荐）** | UEM = **纯 mems 子集投影** + 派生字段（meshDescriptor、results）；**不**另起独立 schemaVersion |
| B2 | 引入 `uemSchemaVersion` 独立轨 |

**默认 B1：** 少分叉、少双写；与 Q5-5 / geometry 双轨已够用。若日后离线草稿强需求再开 B2。

### F-C — 路由形态

| 选项 | 含义 |
| --- | --- |
| **C1（默认推荐）** | **多路由保留**（`/workspace` `/analytic` `/field` `/drive`…），共享同一 Pinia UEM；教学路由后置 |
| C2 | 单 Workspace 壳 + 内嵌面板，弱化多页 |

**默认 C1：** 改动面小、符合「不重写整个前端」；Maxwell 链靠 UEM 粘合，而非一次性 IA 重做。C2 可作后续 UX 收敛。

### F-D（可选拍板）— P0 rebuild 过渡

| 选项 | 含义 |
| --- | --- |
| **D1（默认推荐）** | P0 先 **薄后端 rebuild** 打通「参数→descriptor→Three」，并行开浏览器移植；P1 切本地为主 |
| D2 | P0 直接只做浏览器移植，后端仅金标测试 |

**默认 D1：** 风险更低，先证明 UEM 粘合与视口订阅，再优化延迟。

---

## 5. 非目标

- 不宣称误差达标 / 不宣称 MVP / 不勾 ≤5%、≤3%。  
- **不删** fixture / dry-run 降级路径。  
- **不**重写整个前端；不强制一次收掉多路由。  
- 教学流后置 **≠** 删除教学文档或路由。  
- 不把 `/field` 改成 mems/files 主路径。  
- 不在本文范围改业务大代码；不改 `docs/01`、`docs/02`。  
- STEP/DXF、Wasm AF 全量仍按既有降级/后置口径。

---

## 6. 给角色的一句话

| 角色 | 一句话 |
| --- | --- |
| **Motor** | 请拍板 F-A/B/C（及可选 F-D）；本建议默认 **A1+B1+C1+D1**，Maxwell-first、教学后置。 |
| **Mo-前端** | 落地 `ProjectSession`；Workspace 主路径脱离「只读 static mesh」；Three 订阅 UEM；fixture 仅降级。 |
| **Mo-几何** | 保持 `rebuild_live_geometry` / descriptor 为金标；协助 FE 对拍或薄 HTTP/Wasm 边界；不进求解内核。 |
| **Mo-解析** | 只消费 UEM 导出的 `GeometrySummary`+材料+OP；禁止页面私有几何第二真相。 |
| **Mo-后端** | 权威仍在 mems + OpenAPI；可加薄 geometry rebuild 路由（若 Motor 选 D1）；`/field` 继续 artifacts。 |
| **产品** | 主路径讲 Maxwell 链；教学向导后置保留；对外不把「实时视口」说成 FEM 实时。 |

---

## 附录 A — FE `b71b355` 轻核（知悉）

| 项 | 结论 |
| --- | --- |
| 常量 | `MEMS_SCHEMA_VERSION = '1.0.0'`；写 `MEMS_SCHEMA_VERSION_WRITE`；读接受 `1.0.0` + `1.0.0-draft`（PR #4） |
| `/field` | **PASS**：场图主路径走 Jobs artifacts，**不**经 `getMems` / `assertAcceptedMemsPackage`；钉版不破坏 artifacts 主路径 |
| 缺口 | 无阻塞缺口；仅整包 mems 读写受版本断言约束（符合 Q5-5） |

知悉：后端 nit `6e4a872`（空/绝对 path → 400）；产品 Q5-1/Q5-5 `d054fb5`。

---

## 附录 B — 自查索引（路径）

| 区域 | 路径 |
| --- | --- |
| 路由 | `apps/web/src/router/index.ts` |
| Workspace / fixture | `apps/web/src/views/WorkspaceView.vue`；`apps/web/public/mesh/*` |
| Three | `apps/web/src/components/Viewport3D.vue`；`apps/web/src/lib/meshToThree.ts` |
| Field | `apps/web/src/views/FieldVizView.vue` |
| Analytic | `apps/web/src/views/AnalyticView.vue`；`apps/web/src/lib/analyticSolve.ts` |
| 几何 live | `packages/geometry`；`docs/drafts/几何-Q4plus-live与降级.md` |
| 契约 | `docs/drafts/mems-schema-v1.md`；`Q5-1-mems-files边界.md`；`Q2-材料与解析边界.md` |

---

*架构建议稿结束。待 Motor 拍板分叉后，再拆前端/几何/后端可执行任务；仍不改 01/02 正文。*
