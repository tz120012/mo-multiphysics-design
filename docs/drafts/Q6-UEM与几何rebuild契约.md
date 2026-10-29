# Q6：UEM 与几何 rebuild 契约（锁定稿）

| 字段 | 内容 |
| --- | --- |
| 维护 | Mo-架构 |
| 日期 | 2026-10-29（Asia/Shanghai） |
| 状态 | **锁定**（Q6 基线） |
| 开闸 | Motor tip **`cc3b2d1`**（[Q6-开闸-Motor签字](../qa/Q6-开闸-Motor签字.md)） |
| 分叉拍板 | Motor tip **`be6ed88`** → **A1 + B1 + C2 + D1**（[Q6-架构分叉-Motor拍板](../qa/Q6-架构分叉-Motor拍板.md)；**C2 非 C1**） |
| 建议原稿 | tip `6dafa91` → [Maxwell-first统一工程模型与实时视口](./Maxwell-first统一工程模型与实时视口.md) |
| 仓库 | 仅 `/workspace/mo-platform` |
| 约束 | **不改** `docs/01`、`docs/02` 正文；不改求解核心；禁宣称 MVP；禁勾 ≤5%/≤3%；禁宣称「已对齐 Maxwell」；教学后置 |

> 本文钉死 UEM（会话投影）、几何 rebuild API、C2 单壳接线、改参→求解闭环契约面。  
> 实现可分 tip；契约形与禁令以本文为准。

---

## 1. UEM（B1）

### 1.1 定义

- 前端 Pinia store（建议名 **`useProjectSession`**）：投影 `.mems` **子集** + 派生字段。
- **权威**仍是后端 mems + OpenAPI；UEM = **会话投影**，可丢可重建。
- **不**新引入 `uemSchemaVersion` / 独立 schema 轨（B1）。

### 1.2 切片（最小核）

| 切片 | 内容 |
| --- | --- |
| `projectMeta` | `projectId`、topology、machineType、打开中包的展示元数据 |
| `geometry.params` | 与 mems `geometry/params.json` 一致（camel；长度默认 **mm**，角 **deg**；`poleCount` 权威） |
| `materials` | 材料引用 id + 可选覆盖（解析前 `resolveMaterials`） |
| `excitation` \| `drive` | 工况 / 电调草稿 |
| `meshDescriptor` | 派生；视口订阅源 |
| `geometrySummary` | 派生；供 analytic/FEM 组装 |
| `resultsRefs` | `lastJobId` / `resultRef` 等指针（不替代 artifacts 本体） |
| 脏标记 | `geometryDirty` 等 |

### 1.3 脏标记与快照

- `geometry.params` 变更 → 置 **`geometryDirty=true`**。
- 须经 **rebuild 成功** 后清脏（写回 `meshDescriptor` / `geometrySummary`）。
- **求解**（analytic / FEM / drive）必须用**当前 UEM 快照**组装 payload；禁止各步骤私有默认几何双源。

### 1.4 跨步骤共享（C2，非 C1）

- **Q6 验收主路径** = **单 Workspace 壳**（树 + 属性面板 + Three 视口）。
- 壳内步骤顺序钉死：**几何 → 材料 → 激励 → 网格 → 求解 → 后处理**；各步骤读写**同一** `useProjectSession`。
- 旧多路由（`/analytic` `/field` `/drive` `/compare` 等）允许：
  - 深链打开壳内对应步骤，或
  - 临时重定向 / 嵌入壳内面板；
  - **不得**以「多页 + 共享 Pinia」作为 Q6 一站式验收达标口径（Motor C2）。
- 教学路由后置（可保留；不挡主路径）。

---

## 2. 几何 rebuild API（D1 → A1）

### 2.1 P0 权威路径（同步，秒级）

| 项 | 钉死 |
| --- | --- |
| Method / path | **`POST /api/v1/geometry/rebuild`** |
| 同步性 | **同步 HTTP**；目标秒级；**非** Celery Job、不入 `/jobs` |
| 实现 | `apps/api` 调 **`mo_geometry.rebuild_live_geometry`**（几何包权威） |
| OpenAPI | 写入 `docs/drafts/openapi-v1.yaml`；实现前可标 `x-status: planned-q6` |
| 禁止 | 用 `public/mesh` fixture JSON **冒充** rebuild 成功响应 |

### 2.2 Request

```json
{
  "topology": "RF",
  "machineType": "PMSM",
  "params": { }
}
```

| 字段 | 要求 |
| --- | --- |
| `topology` | 必填；与 params 内 `topology` 一致（`RF` \| `AF`） |
| `machineType` | 可选；与 params / project 对齐（如 `PMSM` \| `ACIM`） |
| `params` | **必填**；形与 mems `geometry/params.json` / `packages/geometry` 一致（camel） |

**单位约定：**

- `params.units.length` 默认 **`mm`**（亦接受 `m`）；`units.angle` 默认 **`deg`**（亦接受 `rad`）。
- 派生 `geometrySummary`（解析侧）为 **SI 米 / snake_case**（几何包既有导出）；`meshDescriptor` 与 FE/examples 既有约定一致。
- **禁止**在 rebuild 响应里 silently 改写单位而不回传 `params.units`。

### 2.3 Response（= `rebuild_live_geometry` 形）

```json
{
  "params": { },
  "meshDescriptor": { },
  "geometrySummary": { },
  "pipelineEntry": { }
}
```

| 字段 | 说明 |
| --- | --- |
| `params` | 规范化后的 mems 几何片段（与包导出一致） |
| `meshDescriptor` | Three / 视口主输入 |
| `geometrySummary` | analytic/FEM 组装用 |
| `pipelineEntry` | 可选；AF-PMSM 等既有导出时附带 |

### 2.4 错误与降级

| 码 | 何时 |
| --- | --- |
| **400** | 校验失败（缺字段、非法 `poleCount`、topology 不一致等）；body 用既有 `Error` |
| **501** | 拓扑/机型本阶段未支持 live rebuild；或实现未齐（`planned-q6`） |
| 降级（客户端） | 无 project / rebuild 失败 / 显式 `?source=fixture` → 可读 public fixture；**UI 不得标「建模完成」** |

### 2.5 P1+（A1）

- 浏览器本地重建为主；本 API 保留为**金标 / 无本地实现时的降级 / CI 对拍**。
- **契约响应形不变**。

---

## 3. 视口接线（给前端 · C2 壳内）

```text
属性面板改 geometry.params
  → 置 geometryDirty
  → debounce（建议 150–300ms）
  → POST /geometry/rebuild（P0）或本地 rebuild（P1+）
  → 写 UEM.meshDescriptor / geometrySummary；清 geometryDirty
  → Three（Viewport3D）订阅 meshDescriptor 更新
```

- fixture **仅降级**（无 project / rebuild 失败 / `?source=fixture`）。
- UI **不得**把 fixture 或静态样例标成「建模完成」。
- **禁止**视口拖拽/滑条与 FEM/analytic Jobs 耦合。

---

## 4. 改参→求解闭环（Q6-3 契约面）

- analytic / FEM：**显式按钮**（或壳内「求解」步骤的明确动作）；默认不自动打 Jobs。
- payload **从 UEM 组装**（`geometrySummary` + materials + OP / fem hint）；**禁止**各页/各步骤私有默认几何双源。
- 成功后：UEM 记 `lastJobId` / `resultRef`（`resultsRefs`）。
- **后处理步骤**内嵌场图：仍走 **Jobs artifacts**（Q5-1）；不改成 mems/files 主路径。
- 不与视口拖拽耦合。

---

## 5. 与 mems 持久化

| 动作 | 钉法 |
| --- | --- |
| 打开工程 | 优先 `GET .../mems/files/geometry/params.json`（Q5-1）；失败再整包抽成员 → **hydrate UEM** |
| rebuild 成功 | **可选**写回会话；**持久化**须产品/前端**显式保存**（整包 `PUT .../mems`） |
| member PUT | **非本门**（Q5-1 已钉只读 GET） |
| 权威 | 包在磁盘/对象存储；UEM 可丢 |

---

## 6. 验收条 / 非目标 / 角色一句话

### 6.1 验收条（契约面 · 非冒烟代勾）

1. 单 Workspace 壳内可切换经典链步骤且共享同一 UEM。  
2. 改参 → rebuild → 视口可见更新（非仅换样例文件）。  
3. 改参后显式求解，payload 来自 UEM；成功后 resultsRefs 可指向 job。  
4. fixture 降级明示；不得冒充 rebuild 成功 / 「建模完成」。  
5. `POST /geometry/rebuild` 同步；响应形对齐 `rebuild_live_geometry`。

### 6.2 非目标

- 教学完成 / US-084  
- 扩大误差门禁或勾 ≤5%/≤3%  
- STEP/OCC  
- 重开 v1.0.0 / Q5 / MVP 争议  
- member 级 PUT  
- 用 Celery 做 rebuild（新分叉，须报 Motor）  
- 另起 UEM schemaVersion（B2，须报）  
- 以 C1 多页粘合顶替 C2 验收

### 6.3 角色一句话

| 角色 | 一句话 |
| --- | --- |
| **架构** | 本契约；分叉基线 A1+B1+C2+D1 |
| **后端** | 实现同步 `POST /api/v1/geometry/rebuild` → `mo_geometry.rebuild_live_geometry`；禁 fixture 冒充 |
| **几何** | 保证 live / descriptor / summary 稳定；对拍金标；不进求解内核 |
| **前端** | C2 单壳 + `useProjectSession` + 视口订阅；禁 fixture=建模完成；求解从 UEM 组装 |
| **测试** | 冒烟：改参见视口变 + 再求解闭环；单壳步骤可走通；未测过不得放行 |

---

## 7. 重大分叉

| 项 | 状态 |
| --- | --- |
| A1+B1+**C2**+D1 | **已采纳 @ Q6**（Motor `be6ed88`）；改口须 Motor 明示 |
| 新分叉须报 Motor | ① 用 Celery/Jobs 做 rebuild；② 另起 UEM schemaVersion；③ 改回强制多路由验收（C1）或其它单壳改口 |

本契约落档时**未见**须 Motor 新拍的额外冲突（C2 已在 `be6ed88` 明示；与产品冻结 IN#1「一站式=单壳」一致）。

---

## 附录 — 对照索引

| 文档 | 用途 |
| --- | --- |
| [Q6-开闸-Motor签字](../qa/Q6-开闸-Motor签字.md) | IN#1–3 开闸 |
| [Q6-架构分叉-Motor拍板](../qa/Q6-架构分叉-Motor拍板.md) | A1+B1+C2+D1 |
| [Maxwell-first…](./Maxwell-first统一工程模型与实时视口.md) | 建议稿（已标 Q6 基线） |
| [几何-Q4plus-live与降级](./几何-Q4plus-live与降级.md) | `rebuild_live_geometry` |
| [Q5-1-mems-files边界](./Q5-1-mems-files边界.md) | 成员读；field≠mems/files |
| [openapi-v1.yaml](./openapi-v1.yaml) | `POST /geometry/rebuild` |
| [Maxwell-缺口对照…](../qa/Maxwell-缺口对照与下一迭代冻结.md) | §C 验收勾选 |

---

*锁定稿结束。实现另 tip；不改 01/02；不改求解核心。*
