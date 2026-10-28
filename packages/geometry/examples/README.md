# 前端消费样例（Q1 mesh / params）

供 **Mo-前端** 将 mesh descriptor 转为 Three.js，无需本机跑 Python。

| 文件 | 用途 |
| --- | --- |
| `radial_pmsm_params.json` | `geometry/params.json` 径向 PMSM 片段 |
| `radial_pmsm_mesh.json` | 对应 mesh descriptor |
| `radial_acim_params.json` / `radial_acim_mesh.json` | 含 `acim` 导条块 |
| `axial_af_pmsm_rfmr_params.json` / `axial_af_pmsm_rfmr_mesh.json` | 轴向 AF-PMSM RFMR |

字段权威对照：`docs/drafts/geometry-mems-字段对照.md`。

## mesh descriptor 约定

- `schemaVersion`: `0.1.0-q1`
- `kind`: `radial` \| `axial`
- `primitives[]`: 当前主要为 `ring` / `sector`（见主 README）
- **不进** `.mems` 必选清单；运行时由参数生成或读本目录快照联调
- **无 CAD**（STEP/DXF = Q2）

调参联调：改 `*params.json` 后应由后端/`mo_geometry` 重算 mesh；Q1 可用本快照先画通。
