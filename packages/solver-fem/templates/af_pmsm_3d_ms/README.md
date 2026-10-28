# Template: AF PMSM 3D — magnetostatic skeleton (`af_pmsm_3d_ms`)

| 项 | 值 |
| --- | --- |
| topology | AF |
| machineType | PMSM |
| dim | 3d |
| solverKernel | elmer（目标） |
| `equationMode` | **`magnetostatic`** |
| meshProfile | `af_pmsm_3d_ms_min`（网格可复用 `af_pmsm_3d` 盒） |

## 口径（硬）

- 本目录 = **磁静力学骨架**，**≠** heat-proxy（`af_pmsm_3d` / `rf_pmsm_2d` 的 HeatEquation **保留另路径**）。
- `pending_calibration: true`；**禁止宣称 FEM ≤3% / MVP**。
- `magnetostaticPathReady: false`：真 Elmer 磁静力学方程 + Maxwell/虚功后处理未关；**不得**提交必然 fail 的冒充成功路径。
- 可冒烟：`python3 packages/solver-fem/smoke/run_magnetostatic_shell.py`（不依赖容器）。

## 文件

| 文件 | 说明 |
| --- | --- |
| `template.json` | 元数据：`equationMode=magnetostatic` 等 |
| `mesh.geo` | 最小盒（自 `af_pmsm_3d` 同源复制；后处理就绪前可换气隙网） |
| `case.sif` | **骨架注释 + TODO**；非可宣称成功的假磁静力学解 |

边界书面：[docs/drafts/Q4plus-5-磁静力学与轴向真值.md](../../../../docs/drafts/Q4plus-5-磁静力学与轴向真值.md)
