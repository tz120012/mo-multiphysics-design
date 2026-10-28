# 前端消费样例（Q1 mesh / params + Q3-2 入口）

供 **Mo-前端** 将 mesh descriptor 转为 Three.js，以及串联解析 / FEM 入口，无需本机跑 Python。

| 文件 | 用途 |
| --- | --- |
| `radial_pmsm_params.json` | `geometry/params.json` 径向 PMSM 片段 |
| `radial_pmsm_mesh.json` | 对应 mesh descriptor |
| `radial_pmsm_geometry_summary.json` | Q3-2：`export_geometry_summary` → GeometrySummary（RF） |
| `radial_acim_params.json` / `radial_acim_mesh.json` | 含 `acim` 导条块 |
| `axial_af_pmsm_rfmr_params.json` / `axial_af_pmsm_rfmr_mesh.json` | 轴向 AF-PMSM RFMR |
| `axial_af_pmsm_rfmr_geometry_summary.json` | Q3-2：AF GeometrySummary |
| `axial_af_pmsm_rfmr_pipeline_entry.json` | Q3-2：`export_axial_pipeline_entry` 全流程入口 |

字段权威对照：`docs/drafts/geometry-mems-字段对照.md`。

## mesh descriptor 约定

- `schemaVersion`: `0.1.0-q1`
- `kind`: `radial` \| `axial`
- `primitives[]`: 当前主要为 `ring` / `sector`（见主 README）
- **不进** `.mems` 必选清单；运行时由参数生成或读本目录快照联调
- **无 CAD**（STEP/DXF = Q2）

## Q3-2 GeometrySummary / pipeline entry

- Summary：snake_case + SI 米；必填 `poles/slots/stack_length_m/airgap_m/rotor_od_m/stator_id_m`
- AF `stack_length_m` = `diskThickness/1000`（单有效盘厚；不乘 diskCount）
- `poles` = `poleCount`（极数，正偶数）；勿双写 polePairs
- Pipeline `femEntryHint.schemaVersion` = `0.1.0-q3-hint`（独立于几何参数 `0.1.0-q1`）
- `analyticSolveStub.schema_version` = `0.0.0-gate0`（对齐 solve.schema）

调参联调：改 `*params.json` 后应由后端/`mo_geometry` 重算 mesh / summary；Q1 可用本快照先画通。
