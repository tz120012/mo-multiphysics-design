# 裁决：geometry / `.mems` 极数与双轨版本

| 项 | 值 |
| --- | --- |
| 日期 | 2026-10-28 |
| 作者 | Mo-架构 |
| 范围 | `docs/drafts` 契约澄清；不改 01/02；不 bump `1.0.0-draft` |

## 结论

1. **极数规范字段**：`poleCount`（极数，正偶数）。电气**极对数** = `poleCount / 2`（派生）。勿在 `geometry/params.json` 双写冲突源。
2. RF：`rotor.poleCount`；AF：`pmsm.poleCount` 同规则。
3. ACIM：`acim.cagePolePairs` **可保持极对数**（笼型文献；Q1 不改名）。并存时校验 soft-check `cagePolePairs == rotor.poleCount/2`（已知不对称）。
4. **KEEP 双轨**：`memsSchemaVersion`（整包）vs `geometry/params.json` `schemaVersion`（几何子 schema，当前 `0.1.0-q1`）。字段对照权威：[geometry-mems-字段对照.md](./geometry-mems-字段对照.md)；勿把完整字段表并入 `mems-schema-v1`。

## 依据

- 实现已存 `poleCount`；文案「极对数」易造成双源真相。
- 整包与几何子 schema 变更节奏不同；对照表已承担字段级映射，直至 Q1-2 JSON Schema。

## 对 Mo-几何 · 前端 · 后端的动作

| 角色 | 动作 |
| --- | --- |
| **Mo-几何** | 继续以 `poleCount` 为唯一几何源；文档/校验注释写清派生极对数；ACIM soft-check 如上；不改名 `cagePolePairs`。 |
| **前端** | UI 若展示「极对数」，显示/编辑时换算自 `poleCount`（或编辑极对数再写回偶数极数）；勿另存冲突字段。 |
| **后端** | 包校验遵循双轨版本；几何片段按对照表 + 本裁决；不要求 bump `memsSchemaVersion`。 |

*澄清性裁决；破坏性字段改名不在本提交。*
