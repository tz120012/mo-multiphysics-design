# packages/geometry — Mo-几何（Q1）

参数化电机几何（径向 RF / 轴向 AF-PMSM）与 **Three.js 协作网格描述**。  
维护：Mo-几何 · 仅 `/workspace/mo-platform`。

| Schema | 值 |
| --- | --- |
| 几何参数 `schemaVersion` | `0.1.0-q1` |
| 网格描述 `schemaVersion` | `0.1.0-q1` |
| 对齐 | `docs/drafts/mems-schema-v1.md`、`docs/drafts/geometry-mems-字段对照.md`、`docs/drafts/几何范围.md` |

## Q1 vs Q2

| 能力 | Q1（本包） | Q2+ |
| --- | --- | --- |
| 径向 RF 参数（BLDC/PMSM/ACIM） | ✅ Q1-4 | 硬化契约 |
| 轴向 AF-PMSM（RFMR/FRMF） | ✅ Q1-5 | 全流程 UI |
| ACIM 导条参数位 | ✅ Q1-7 | 与解析/材料联动 |
| Three.js mesh descriptor JSON | ✅ | — |
| STEP / DXF（CadQuery/OCC） | ❌ 不做 | ✅ 必交可演示 |
| Wasm / FEM 网格 | ❌ | 分属解析 / 有限元 |

几何参数 JSON → **前端 / 后端 / `.mems`**；**不进 Wasm**。


## 极数约定（架构裁决）

- 持久化唯一源：`poleCount`（正偶数，极数）
- 电气极对数派生：`pole_pairs_from_pole_count(poleCount)` → `poleCount / 2`（UI 可显示，勿另存冲突字段）
- ACIM：`cagePolePairs` 保持极对数语义不改名；与 `rotor.poleCount/2` soft-check
- 详见 `docs/drafts/裁决-geometry-mems-poleCount.md`

## 安装与测试

```bash
cd packages/geometry
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## 公共 API

```python
from mo_geometry import (
    default_radial_bldc,
    default_radial_pmsm,
    default_radial_acim,
    default_axial_af_pmsm,
    validate_radial,
    validate_axial,
    to_mems_radial_fragment,
    to_mems_axial_fragment,
    build_radial_mesh_descriptor,
    build_axial_mesh_descriptor,
)
```

- `validate_*` → `list[str]` 错误（含可选 `warning:` 前缀软约束）
- `to_mems_*_fragment` → 可写入 `geometry/params.json` 的稳定 dict
- `build_*_mesh_descriptor` → 前端可转 Three.js `BufferGeometry` 的图元 JSON

## 样例 JSON（免 Python）

见 [`examples/`](examples/)：径向 PMSM/ACIM、轴向 AF-PMSM 的 `params` + `mesh` 快照，供 Mo-前端先接 Three.js。

字段对照：[`docs/drafts/geometry-mems-字段对照.md`](../../docs/drafts/geometry-mems-字段对照.md)。

## 前端如何消费 mesh descriptor

本包**不**依赖 Three.js。描述符形如：

```json
{
  "schemaVersion": "0.1.0-q1",
  "kind": "radial",
  "units": { "length": "mm", "angle": "deg" },
  "meta": { "slotCount": 18, "poleCount": 6, "...": "..." },
  "primitives": [
    {
      "type": "ring",
      "name": "stator_yoke",
      "innerRadius": 35,
      "outerRadius": 40,
      "height": 25,
      "z": 0,
      "radialSegments": 72,
      "thetaSegments": 72
    },
    {
      "type": "sector",
      "name": "stator_tooth_0",
      "innerRadius": 25.5,
      "outerRadius": 35,
      "height": 25,
      "startAngleDeg": 2,
      "sweepAngleDeg": 8,
      "z": 0,
      "segments": 8
    }
  ]
}
```

建议映射：

| `type` | Three.js 思路 |
| --- | --- |
| `ring` | `LatheGeometry` / 环形挤出 / `CylinderGeometry` 差集近似 |
| `sector` | `Shape` 扇环 + `ExtrudeGeometry`，或扇形 `BufferGeometry` |

参数变更（槽数、内外径等）会改变 `primitives` 数量与尺寸；前端可用命令模式做 Undo/Redo（Q1-6）。

## 任务对照

| 编号 | 内容 |
| --- | --- |
| Q1-4 | `radial.py` + `build_radial_mesh_descriptor` |
| Q1-5 | `axial.py` + `build_axial_mesh_descriptor`（非 PMSM 仅枚举预留） |
| Q1-7 | `acim.py` 可选块，`machineType=ACIM` 时必填 |

范围草案：`docs/drafts/几何范围.md`。
