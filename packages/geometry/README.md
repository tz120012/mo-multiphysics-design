# packages/geometry — Mo-几何（Q1 + Q3 入口 + Q4+ live）

参数化电机几何（径向 RF / 轴向 AF-PMSM）与 **Three.js 协作网格描述**，以及 **解析 GeometrySummary / AF 全流程入口 / live 重建**。  
维护：Mo-几何 · 仅 `/workspace/mo-platform`。

| Schema | 值 |
| --- | --- |
| 几何参数 `schemaVersion` | `0.1.0-q1`（保留） |
| 网格描述 `schemaVersion` | `0.1.0-q1` |
| FEM 入口 hint `schemaVersion` | `0.1.0-q3-hint`（独立版本；不做网格） |
| SolveRequest `schema_version` | `0.0.0-gate0`（只读对齐 solver-analytic） |
| 对齐 | `docs/drafts/mems-schema-v1.md`、`docs/drafts/geometry-mems-字段对照.md`、`docs/drafts/几何范围.md`、`docs/drafts/Q2-材料与解析边界.md` 附录 A |

## Q1 vs Q2 / Q3

| 能力 | Q1（本包） | Q2+ | Q3-2（本包） |
| --- | --- | --- | --- |
| 径向 RF 参数（BLDC/PMSM/ACIM） | ✅ Q1-4 | 硬化契约 | — |
| 轴向 AF-PMSM（RFMR/FRMF） | ✅ Q1-5 | 全流程 UI | ✅ 几何入口 API |
| ACIM 导条参数位 | ✅ Q1-7 | 与解析/材料联动 | — |
| Three.js mesh descriptor JSON | ✅ | — | — |
| `export_geometry_summary` | — | 契约钉表 | ✅ |
| `export_axial_pipeline_entry` | — | — | ✅ AF 串联 |
| `rebuild_live_geometry` | — | — | ✅ Q4+ live |
| STEP / DXF（CadQuery/OCC） | ❌ | 曾要求可演示 | **Q4+ 明确降级**（见降级短文） |
| Wasm / FEM 求解 | ❌ | 分属解析 / 有限元 | ❌ 仅 hint；AF Wasm 未交付 |

几何参数 JSON → **前端 / 后端 / `.mems`**；**不进 Wasm**。本包**不写**解析求解 / FEM 求解。

## 极数约定（架构裁决）

- 持久化唯一源：`poleCount`（正偶数，极数）
- 电气极对数派生：`pole_pairs_from_pole_count(poleCount)` → `poleCount / 2`（UI 可显示，勿另存冲突字段）
- GeometrySummary.`poles` = `poleCount`（极数）；**禁止**往 params/mems 双写 `polePairs`
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
    export_geometry_summary,
    export_axial_pipeline_entry,
    rebuild_live_geometry,
)
```

- `validate_*` → `list[str]` 错误（含可选 `warning:` 前缀软约束）
- `to_mems_*_fragment` → 可写入 `geometry/params.json` 的稳定 dict
- `build_*_mesh_descriptor` → 前端可转 Three.js `BufferGeometry` 的图元 JSON
- `export_geometry_summary(params)` → 解析 `GeometrySummary`（snake_case + SI 米）；非法则 `ValueError`
- `export_axial_pipeline_entry(params)` → AF-PMSM 串联包：`geometryParams` / `geometrySummary` / `meshDescriptor` / `analyticSolveStub` / `femEntryHint`
- `rebuild_live_geometry(params)` → `{params, meshDescriptor, geometrySummary[, pipelineEntry]}`（AF-PMSM 附 pipeline）

### AF `stack_length_m` / 扩展字段约定

盘式无径向叠长时，有效磁路轴向长度钉为**单有效盘厚**：

```text
stack_length_m = disk_thickness_m = pmsm.diskThickness / 1000   # units.length=mm
outer_radius_m = outerDiameter/2 → m
inner_radius_m = innerDiameter/2 → m
disk_count = pmsm.diskCount
n_planes = 4  # 默认；与 axial_planes.DEFAULT_N_PLANES 一致；params.nPlanes 可覆盖
magnet_arc_ratio = magnetSectorAngle/180  # 可选，∈ (0,1]
```

不按 `diskCount` 累乘。构型等仍见 `femEntryHint`。对齐说明：`docs/drafts/几何-Q4plus-live与降级.md`。

## 样例 JSON（免 Python）

见 [`examples/`](examples/)：径向 PMSM/ACIM、轴向 AF-PMSM 的 `params` + `mesh` + `geometry_summary` / `pipeline_entry`。用 `python -m mo_geometry.rebuild_examples` 从 defaults live 重写。FE `public/geometry` 静态拷贝 ≠ 本包 live（见 examples README）。

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
    }
  ]
}
```

建议映射：

| `type` | Three.js 思路 |
| --- | --- |
| `ring` | `LatheGeometry` / 环形挤出 / `CylinderGeometry` 差集近似 |
| `sector` | `Shape` 扇环 + `ExtrudeGeometry`，或扇形 `BufferGeometry` |

### 前端消费 Q3-2 入口（AF）

```text
params (AF-PMSM)
  → export_axial_pipeline_entry
       ├─ geometryParams     → 写 .mems geometry/params.json / UI 状态
       ├─ meshDescriptor     → Three.js
       ├─ geometrySummary    → 填入 analyticSolveStub.geometry 或单独 POST
       ├─ analyticSolveStub  → POST /solver/analytic/solve（材料/工况由 FE 填实）
       └─ femEntryHint       → 交给 Mo-有限元（schemaVersion 0.1.0-q3-hint；无网格）
```

## 任务对照

| 编号 | 内容 |
| --- | --- |
| Q1-4 | `radial.py` + `build_radial_mesh_descriptor` |
| Q1-5 | `axial.py` + `build_axial_mesh_descriptor`（非 PMSM 仅枚举预留） |
| Q1-7 | `acim.py` 可选块，`machineType=ACIM` 时必填 |
| Q3-2 | `summary.py`：`export_geometry_summary` + `export_axial_pipeline_entry` |
| Q4+-4 | AF summary 对齐 axial_planes；`rebuild_live_geometry`；STEP/DXF 降级短文 |

范围草案：`docs/drafts/几何范围.md`；降级：`docs/drafts/几何-Q4plus-live与降级.md`。
