# Q1-6 History 最小契约（Undo/Redo）

| 项 | 值 |
| --- | --- |
| 状态 | Q1 正式草案口径；**不 bump** API / mems 主版本 |
| 日期 | 2026-10-28 |
| 作者 | Mo-架构 |
| 读者 | **Mo-前端**（命令栈实现）；Motor / Mo-后端对齐形状 |
| OpenAPI | [`openapi-v1.yaml`](./openapi-v1.yaml) `History*`（`1.0.0-draft`） |
| Mems | [`mems-schema-v1.md`](./mems-schema-v1.md) → `history/stack.json` |

> 位于 `docs/drafts/`，**不修改** `docs/01` / `docs/02`。本草案为已有 History 桩**补语义**，不新增服务端 append API。

---

## 1. Q1 原则

- **客户端权威**：Undo/Redo 在前端命令模式执行；服务端 Q1 **仅对齐响应形状**（可空桩，可不改工程状态）。
- **线性栈**（非分支树）足够过 Q1-6；`cursor` = 当前可 redo 边界（见 §2）。
- 保存工程时把栈摘要写入 `.mems` 的 `history/stack.json`（随 **PUT mems** 走）；**不要求**独立 history 持久化 API。
- **Local-first**：FE **不得**等待 `POST .../undo` / `.../redo` HTTP 成功后再改 UI；HTTP 可忽略或仅做形状校验。

---

## 2. 命令栈模型

```
entries: HistoryEntry[]   # 时间正序，index 0 = 最早
cursor: number            # 指向「下一条将 redo 的位置」；undo 后 cursor 减小
# 不变量：0 <= cursor <= entries.length
# undo：若 cursor > 0 → cursor--，apply inverse of entries[cursor]
# redo：若 cursor < len → apply entries[cursor]，cursor++
# 新命令：截断 entries.splice(cursor)，push 新 entry，cursor = entries.length
```

| 状态 | 含义 |
| --- | --- |
| `cursor == entries.length` | 在栈顶；无 redo；undo 可用（若 `cursor > 0`） |
| `cursor == 0` | 全 undo；无 undo；redo 可用（若有 entries） |
| `0 < cursor < length` | 中间：两侧皆可 |

---

## 3. HistoryEntry 字段（钉死）

| field | type | required | notes |
| --- | --- | --- | --- |
| `id` | string (uuid) | yes | 稳定命令 ID |
| `commandType` | enum string | yes | 见下表 |
| `summary` | string | yes | UI 一行；中文/英文均可 |
| `createdAt` | ISO-8601 | yes | |
| `payload` | object | yes（真实命令） | 正向参数；须可重放 |
| `inverse` | object | recommended Q1 | 撤销所需；若缺则 FE 用快照策略 |

### `commandType` Q1 最小集

| commandType | payload 约定 | 说明 |
| --- | --- | --- |
| `geometry.params.set` | `{ path, before, after }` 或完整 params patch | 几何参数变更主路径 |
| `project.meta.set` | name / topology / machineType 等 | 少用 |
| `noop` | `{}` 或任意 | 仅测试 / 服务端桩 |

示例：

```json
{
  "id": "a1b2c3d4-e5f6-4789-a012-3456789abcde",
  "commandType": "geometry.params.set",
  "summary": "设置 rotor.outerDiameter = 80",
  "createdAt": "2026-10-28T04:00:00Z",
  "payload": {
    "path": "rotor.outerDiameter",
    "before": 78,
    "after": 80
  },
  "inverse": {
    "path": "rotor.outerDiameter",
    "before": 80,
    "after": 78
  }
}
```

---

## 4. `.mems` 落盘

路径：`history/stack.json`

```json
{
  "schemaVersion": "0.1.0-q1-history",
  "entries": [],
  "cursor": 0
}
```

- 与包级 `memsSchemaVersion`（`project.json`）**双轨**：本文件自带子 schema `schemaVersion`，类比 `geometry/params.json`。
- Q1 样例包若尚未含 `history/`，允许 **空栈启动**（缺文件或 `entries: []` + `cursor: 0`）。
- 同步靠 mems **PUT/下载**；不另开 history blob API。

---

## 5. API 桩形状（已有；语义澄清）

基路径：`/api/v1/projects/{id}`（OpenAPI 相对 `/api/v1`）。

| 方法 | 路径 | 响应 | Q1 语义 |
| --- | --- | --- | --- |
| `GET` | `.../history` | `{ entries, cursor }` | 可恒空；FE 未上传则空 |
| `POST` | `.../history/undo` | `{ cursor, entry }` | **不强制**服务端改状态；FE 本地 undo 后可忽略或校验形状 |
| `POST` | `.../history/redo` | 同上 | 同上 |

- **不新增** 服务端 append / push 命令 API 于 Q1（避免双写）；命令入栈仅在 FE，落盘靠 mems PUT。
- 后端现有 stub：list 空列表；undo/redo 返回占位 `noop` entry — **符合**本契约。

**Clarify（给 Mo-前端）**：UI 变更以本地命令栈为准；**不要**把 undo/redo HTTP 当作状态机真相源。

---

## 6. 前端验收最小条

1. 改一个几何参数 → push `geometry.params.set` → **Undo** 恢复 → **Redo** 再应用。
2. Undo 后发**新命令** → 截断 redo 尾（`splice(cursor)` 再 push）。
3. 保存 / 加载 `.mems` 后 `history/stack.json` 可恢复栈；若 Q1-2 样例无 history，允许空栈启动。

---

## 7. 与 OpenAPI

- 形状权威：`openapi-v1.yaml` → `components.schemas.HistoryEntry` 及 `GET/POST .../history*`。
- 本草案**只加语义**（cursor 含义、commandType 枚举、`inverse`、local-first、mems 落盘），**不 bump** `info.version`（仍为 `1.0.0-draft`）。
- OpenAPI 内 HistoryEntry 描述可引用本文件并补充 `commandType` 示例枚举（澄清性编辑，仍 1.0.0-draft）。

---

*Q1-6 最小契约。分支树 / 服务端权威栈 / append API 均不在本 Q。*
