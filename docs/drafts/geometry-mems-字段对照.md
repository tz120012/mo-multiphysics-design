# geometry ↔ `.mems` 字段对照（短文）

| 项 | 值 |
| --- | --- |
| 状态 | **草案** |
| 对齐 | `docs/drafts/mems-schema-v1.md`（`1.0.0-draft`）；实现 `packages/geometry`（`GEOMETRY_SCHEMA_VERSION = 0.1.0-q1`） |
| 范围 | 仅 `geometry/params.json` 与 `project.json` 拓扑/机型镜像；**无 CAD / STEP / DXF** |
| 日期 | 2026-10-28 |
| 作者 | Mo-几何 |

---

## 1. 包内落点

| `.mems` 路径 | 来源 API | 说明 |
| --- | --- | --- |
| `project.json` → `topology` / `machineType` / `units` | 与几何片段**同值镜像** | 包级索引；改几何时应同步写回（由 FE/BE 命令负责） |
| `geometry/params.json` | `to_mems_radial_fragment` / `to_mems_axial_fragment` | **唯一**几何权威参数文件（Q1 单文件） |
| （不入 `.mems`）mesh descriptor | `build_*_mesh_descriptor` | 运行时给 Three.js；可缓存但不进 Q1 必选清单 |
| `materials/` | 仅引用 ID | ACIM `barMaterialId` / `endRingMaterialId` 指向材料库，不内嵌曲线 |

---

## 2. 版本字段关系

| 字段 | 位置 | 当前值 | 备注 |
| --- | --- | --- | --- |
| `memsSchemaVersion` | `project.json` / `manifest.json` | `1.0.0-draft` | 整包契约（架构） |
| `schemaVersion` | `geometry/params.json` | `0.1.0-q1` | 几何子 schema（Mo-几何） |

破坏性改几何字段名/枚举语义 → bump `0.1.0-q1`，并评估是否触发 `memsSchemaVersion` Gate。

---

## 3. 公共枚举（与 mems-schema-v1 一致）

| 概念 | mems / geometry 取值 |
| --- | --- |
| 拓扑 | `RF` \| `AF` |
| 机型 | `BLDC` \| `PMSM` \| `ACIM` |
| 单位（geometry `units`） | `length`: `mm`\|`m`；`angle`: `deg`\|`rad`（与 project.units 应对齐） |

---

## 4. 径向 RF → `geometry/params.json`

对应 mems-schema-v1 §3「径向 RF」大纲。

| mems 大纲用语 | JSON 路径（geometry） | 类型 / 枚举 | 备注 |
| --- | --- | --- | --- |
| 拓扑标记 | `topology` | `"RF"` | 恒定 |
| 机型 | `machineType` | `BLDC`\|`PMSM`\|`ACIM` | |
| 转子型式 | `rotorTopology` | `inner`\|`outer` | |
| 定子内外径 / 叠长 | `stator.innerDiameter` / `outerDiameter` / `stackLength` | number | 默认单位 mm |
| 槽数 / 槽形 | `stator.slotCount` / `slotShape` | int；`straight`\|`skewed`\|`fan` | 槽形=直/斜/扇形 |
| 齿轭 | `stator.toothWidth` / `yokeHeight` | number | |
| 斜槽角 | `stator.skewAngle` | number \| `null` | 可选 |
| 转子内外径 | `rotor.innerDiameter` / `outerDiameter` | number | |
| 磁钢拓扑 | `rotor.magnetTopology` | `SPM`\|`IPM` | 表贴/内置占位；ACIM 仍保留兼容 |
| 极数 | `rotor.poleCount` | int | mems「极对数」相关：当前存**极数**；极对数 = poleCount/2（调用方换算） |
| 气隙 / 轴向有效长 | `airgap` / `axialActiveLength` | number | |
| 单位 | `units` | object | |
| **ACIM 导条** | `acim` | object；`machineType=ACIM` **必填** | 见下表 |

### 4.1 ACIM 块（Q1-7）

| mems 大纲 | JSON 路径 | 说明 |
| --- | --- | --- |
| 导条槽形 | `acim.barSlotShape` | `rectangular`\|`oval`\|`closed_slot`\|`open_slot` |
| 导条截面 | `acim.barCrossSection.width` / `.height` | |
| 端环截面 | `acim.endRingSection.width` / `.height` | |
| 材料引用 | `acim.barMaterialId` / `endRingMaterialId` | → `materials/` 或材料服务 ID |
| 笼型极对数 | `acim.cagePolePairs` | 槽配合 soft warning 占位 |

---

## 5. 轴向 AF → `geometry/params.json`

对应 mems-schema-v1 §3「轴向 AF」。Q1 **仅 AF-PMSM 展开字段树**。

| mems 大纲用语 | JSON 路径 | 类型 / 枚举 | 备注 |
| --- | --- | --- | --- |
| 拓扑标记 | `topology` | `"AF"` | |
| 机型 | `machineType` | `BLDC`\|`PMSM`\|`ACIM` | 非 PMSM：**禁止**带 `pmsm` 完整树 |
| 盘式结构 | `config` | `RFMR`\|`FRMF` | 单定双转 / 双定单转 |
| 内外径 | `pmsm.innerDiameter` / `outerDiameter` | number | 仅 PMSM |
| 盘数 | `pmsm.diskCount` | int | |
| 气隙 / 盘厚 | `pmsm.airgap` / `diskThickness` | number | mems「轴向厚度」→ `diskThickness` |
| 磁钢扇区角 | `pmsm.magnetSectorAngle` | number (0,180] deg | 绕组/磁钢分区占位之一 |
| 槽 / 极 | `pmsm.slotCount` / `poleCount` | int | |
| 单位 | `units` | object | |

---

## 6. 写入约定（FE / BE）

1. 校验：`validate_radial` / `validate_axial`（返回列表；`warning:` 前缀为 soft）。  
2. 序列化：`to_mems_*_fragment` → 写入 zip 内 `geometry/params.json`。  
3. 同步：`project.json.topology` / `machineType` / `units` 与片段顶栏一致。  
4. 可视化：mesh descriptor **不**替代 `params.json`；导出 CAD 不在本对照范围（Q2）。

### 最小径向片段形状（示意）

```json
{
  "schemaVersion": "0.1.0-q1",
  "topology": "RF",
  "machineType": "PMSM",
  "units": { "length": "mm", "angle": "deg" },
  "rotorTopology": "inner",
  "stator": {
    "innerDiameter": 51.0,
    "outerDiameter": 80.0,
    "stackLength": 25.0,
    "slotCount": 18,
    "slotShape": "straight",
    "toothWidth": 4.5,
    "yokeHeight": 5.0,
    "skewAngle": null
  },
  "rotor": {
    "innerDiameter": 15.0,
    "outerDiameter": 50.0,
    "magnetTopology": "SPM",
    "poleCount": 6
  },
  "airgap": 0.5,
  "axialActiveLength": 25.0
}
```

---

## 7. 已知待对齐（非阻塞）

1. mems 文案「极对数」vs 实现 `poleCount`（极数）— 建议架构在字段级 JSON Schema 中二选一钉死。  
2. `geometry.schemaVersion`（`0.1.0-q1`）与 `memsSchemaVersion`（`1.0.0-draft`）双轨 — 样例包生成时两处都写。  
3. 轴向「绕组分区」除 `magnetSectorAngle` 外的绕组字段 — Q1 未建，后续扩展为可选。

---

*短文结束。无 CAD。修订经 Motor / Mo-架构。*
