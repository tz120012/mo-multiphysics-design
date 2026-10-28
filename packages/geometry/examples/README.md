# 前端消费样例（Q1 mesh / params + Q3 入口 + Q4+ live 重建）

供 **Mo-前端** 将 mesh descriptor 转为 Three.js，以及串联解析 / FEM 入口，无需本机跑 Python。

| 文件 | 用途 |
| --- | --- |
| `radial_pmsm_params.json` | `geometry/params.json` 径向 PMSM 片段 |
| `radial_pmsm_mesh.json` | 对应 mesh descriptor |
| `radial_pmsm_geometry_summary.json` | `export_geometry_summary` → GeometrySummary（RF） |
| `radial_acim_params.json` / `radial_acim_mesh.json` | 含 `acim` 导条块 |
| `axial_af_pmsm_rfmr_params.json` / `axial_af_pmsm_rfmr_mesh.json` | 轴向 AF-PMSM RFMR |
| `axial_af_pmsm_rfmr_geometry_summary.json` | AF GeometrySummary（含半径/盘厚/`n_planes` 等） |
| `axial_af_pmsm_rfmr_pipeline_entry.json` | `export_axial_pipeline_entry` 全流程入口 |

字段权威对照：`docs/drafts/geometry-mems-字段对照.md`。

## FE 静态 public vs 本包 live rebuild

| 路径 | 含义 |
| --- | --- |
| FE `apps/web/public/geometry/*` | 前端静态拷贝 / 联调快照（**非**本包运行时 live） |
| 本目录 `examples/` | 由 **live** 路径从 `default_*` 重生成的可演示样例 |

重建（证明 live 可重生成样例）::

```bash
cd packages/geometry
source .venv/bin/activate
python -m mo_geometry.rebuild_examples
# 或：python scripts/rebuild_examples.py
```

浏览器内 remesh：由 FE 调后端调用 `rebuild_live_geometry` / `export_*`，或照抄 descriptor；**几何不改** `apps/web`。

## mesh descriptor 约定

- `schemaVersion`: `0.1.0-q1`
- `kind`: `radial` \| `axial`
- `primitives[]`: 当前主要为 `ring` / `sector`（见主 README）
- **不进** `.mems` 必选清单；运行时由参数生成或读本目录快照联调
- **无 CAD**（STEP/DXF 本阶段降级，见 `docs/drafts/几何-Q4plus-live与降级.md`）

## GeometrySummary / pipeline entry

- Summary：snake_case + SI 米；必填 `poles/slots/stack_length_m/airgap_m/rotor_od_m/stator_id_m`
- AF 扩展：`outer_radius_m` / `inner_radius_m`（直径÷2）、`disk_thickness_m`（= `stack_length_m`）、`disk_count`、`n_planes`（默认 4）、可选 `magnet_arc_ratio`
- AF `stack_length_m` = `diskThickness→m`（单有效盘厚；不乘 diskCount）
- `poles` = `poleCount`（极数，正偶数）；勿双写 polePairs
- Pipeline `femEntryHint.schemaVersion` = `0.1.0-q3-hint`
- `analyticSolveStub.schema_version` = `0.0.0-gate0`；`geometry` 与 `geometrySummary` 同内容
