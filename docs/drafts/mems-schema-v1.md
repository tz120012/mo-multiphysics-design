# `.mems` 工程包边界草案（schema v1 / `1.0.0-draft`）

| 项 | 值 |
| --- | --- |
| Schema | `1.0.0-draft`（对应 `project.json` 字段 `memsSchemaVersion`） |
| 依据 | `docs/01-任务书-v2.md` §6；`docs/02` Q1-2 |
| 状态 | **Q1 正式草案口径**；Q1 验收前可修订，破坏性变更走 Gate |
| 日期 | 2026-10-28 |
| 作者 | Mo-架构 |

> 本文件位于 `docs/drafts/`，**不修改** 01/02。与 `openapi-v1.yaml` 对齐，供 Mo-后端 / Mo-前端 Q1 契约。

---

## 1. 容器

- **格式**：zip 容器（扩展名 `.mems`）。
- **编码**：文本 JSON 使用 UTF-8；路径分隔符统一 `/`。
- **必选顶层条目**（来自 01 §6）：

```
project.json
geometry/
materials/
solver/
  analytic/
  fem/
drive/
results/
history/
manifest.json
```

空目录在 zip 中可用 `.gitkeep` 或空 JSON 占位；导入时缺失必选路径视为非法包。

---

## 2. `project.json` 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string (UUID) | 工程稳定 ID |
| `name` | string | 显示名称 |
| `memsSchemaVersion` | string | Q1 草案固定为 `"1.0.0-draft"`；破坏性变更必须 bump |
| `topology` | enum | `RF` \| `AF` |
| `machineType` | enum | `BLDC` \| `PMSM` \| `ACIM` |
| `units` | object | 单位制（长度、角度、磁密等约定） |
| `createdAt` | string (ISO-8601) | 创建时间 |
| `updatedAt` | string (ISO-8601) | 最近修改时间 |

可选扩展（草案不强制）：`description`、`ownerId`、`tags`。

### 最小示例

```json
{
  "id": "11111111-2222-4333-8444-555555555555",
  "name": "demo-rf-pmsm",
  "memsSchemaVersion": "1.0.0-draft",
  "topology": "RF",
  "machineType": "PMSM",
  "units": {
    "length": "mm",
    "angle": "deg",
    "magneticFluxDensity": "T",
    "current": "A",
    "temperature": "C"
  },
  "createdAt": "2026-10-28T03:00:00Z",
  "updatedAt": "2026-10-28T03:00:00Z"
}
```

---

## 3. `geometry/` — 拓扑相关参数大纲

路径建议：`geometry/params.json`（单文件）或按域拆分；Q1 以单文件为主。

### 径向 RF

- 转子型式：`inner` \| `outer`
- 定/转子槽极：槽数、**极数** `poleCount`（正偶数；电气**极对数** = `poleCount / 2`，派生量，勿在 geometry/params 双写冲突源）、槽形（直/斜/扇形）
- 齿轭、气隙、叠长、内外径
- 磁钢拓扑（表贴/内置等占位枚举）
- **ACIM**：导条截面、槽形、端环截面与材料引用占位字段（可无求解值；对齐 Q1-7）；`acim.cagePolePairs` 可保持笼型文献用语**极对数**（Q1 不改名；若与 `rotor.poleCount` 并存，校验器 soft-check `cagePolePairs == rotor.poleCount/2`）

### 轴向 AF

- 盘式结构：`RFMR`（单定双转）\| `FRMF`（双定单转）
- 内外径、盘数、气隙、轴向厚度
- 绕组与磁钢分区参数占位
- **极数**：`pmsm.poleCount`（正偶数；极对数 = `poleCount / 2`，同径向规则）

字段级 JSON Schema 在 Q1-2 样例包中细化；本草案钉边界与命名空间。字段级映射权威见同目录 [geometry-mems-字段对照.md](./geometry-mems-字段对照.md)。

---

## 4. `materials/`

- 引用标准库材料 ID（硅钢 B-P、永磁退磁曲线、线圈、ACIM 导条）
- 允许 `custom/` 下自定义曲线 JSON（B-H / B-P / 退磁等）
- 包内仅存引用 + 自定义覆盖；完整库由 API Materials 服务提供（**Q2 CRUD**；Q1 仅 list/get 桩）

---

## 5. `solver/` 桩

| 路径 | 职责 |
| --- | --- |
| `solver/analytic/` | 解析输入/输出快照（MEC / 多平面 / ACIM 等效电路）；可由客户端 Wasm 或 `packages/solver-analytic` 写入 |
| `solver/fem/` | FEM 工况、网格句柄、结果索引；**不在 Gate0/Q1 实现求解**，仅保留目录与空索引 JSON |

---

## 6. `drive/`、`results/`、`history/`、`manifest.json`

| 路径 | 说明 |
| --- | --- |
| `drive/` | 电调与驱动工况定义（方波 / FOC / V/f + 感应 FOC）；Q1 可空 |
| `results/` | 二进制缓存（场量切片、效率 Map、波形）；大文件；checksum 入 manifest |
| `history/` | Undo/Redo 线性栈摘要：`history/stack.json`（前端命令模式写入；随 PUT mems）；契约见 [history-契约-q1-6.md](./history-契约-q1-6.md) |
| `manifest.json` | 文件清单与校验和（建议 SHA-256） |

### `manifest.json` 最小示例

```json
{
  "memsSchemaVersion": "1.0.0-draft",
  "generatedAt": "2026-10-28T03:00:00Z",
  "files": [
    {
      "path": "project.json",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size": 0
    },
    {
      "path": "geometry/params.json",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size": 0
    }
  ]
}
```

（示例 checksum 为占位；真实包须对实际字节计算。）

---

## 7. 几何子 schema 与字段对照

**双轨版本（KEEP）**：

| 字段 | 位置 | 职责 |
| --- | --- | --- |
| `memsSchemaVersion` | `project.json` / `manifest.json` | 整包契约 |
| `schemaVersion` | `geometry/params.json` | 几何子 schema（当前 `0.1.0-q1`） |

字段级映射权威在 Q1-2 JSON Schema 落地前，以同目录 **[geometry-mems-字段对照.md](./geometry-mems-字段对照.md)** 为准；**勿**把完整字段表并入本文。

**极数规则（`poleCount`）**：

- 几何 JSON 规范字段为 **`poleCount`（极数，正偶数）**；电气极对数 = `poleCount / 2`（派生，勿双写冲突源）。
- RF：`rotor.poleCount`；AF：`pmsm.poleCount`。
- ACIM：`acim.cagePolePairs` 可保持极对数（笼型文献）；与 `rotor.poleCount` 并存时 soft-check `cagePolePairs == rotor.poleCount/2`（已知不对称，本提交不改名）。
- 裁决备忘：[裁决-geometry-mems-poleCount.md](./裁决-geometry-mems-poleCount.md)。

---

## 8. 所有权（Ownership）

| 组件 | 职责 |
| --- | --- |
| **API（Mo-后端）** | 持久化 `.mems` blob + 元数据（Project / MemsMeta）；提供 upload/download/import/export |
| **Wasm / `packages/solver-analytic`** | 写入 `solver/analytic/` 快照；不直接改 Project 行（经 API 或本地包回写） |
| **FEM worker（Q3）** | 写入 `solver/fem/` 与 `results/` 索引/切片；经 Jobs 异步回传 |
| **前端** | Undo/Redo 写入 `history/`；几何参数变更经命令模式；本地可先改再 PUT 整包 |

---

## 9. 破坏性变更策略

1. 任何删除/重命名必填字段、更改枚举语义、更改容器顶层布局 → **bump `memsSchemaVersion`**。
2. 须附迁移说明（旧包 → 新包）并经 **Gate 评审**（架构建议 + Motor 确认）。
3. 仅新增可选字段可为同主版本内的兼容扩展（仍建议次版本号递增并在 OpenAPI/MemsMeta 声明）。
4. Q1 验收可将 `1.0.0-draft` 钉为 `1.0.0`（去掉 `-draft`）而不改布局，则不视为破坏性变更。

---

## 10. 与 OpenAPI 的衔接

见同目录 `openapi-v1.yaml`：

- Q1 对齐：鉴权占位、项目 CRUD、`.mems` 上下载/导入导出、history undo/redo 占位
- Materials / Jobs：标为 Q2/Q3 薄桩

---

*Q1 正式草案。样例 `.mems` 包与字段级 JSON Schema 在 Q1-2 补齐。*
