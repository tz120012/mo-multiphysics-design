# Template: AF PMSM 3D — magnetostatic true path (`af_pmsm_3d_ms`)

| 项 | 值 |
| --- | --- |
| topology | AF |
| machineType | PMSM |
| dim | 3d |
| solverKernel | elmer |
| `equationMode` | **`magnetostatic`** |
| meshProfile | `af_pmsm_3d_ms_min`（PM/线圈 + 气隙 + 铁三层盒） |
| Elmer 方程 | WhitneyAVSolver + MagnetoDynamicsCalcFields |
| 后处理 | Component magnetic force → `axialForceN`（Fz）；来源 **maxwell** |

## 口径（硬）

- 本目录 = **真磁静力学可执行路径**，**≠** heat-proxy（`af_pmsm_3d` / `rf_pmsm_2d` 的 HeatEquation **保留不动**）。
- `pending_calibration: true`；**禁止宣称 FEM ≤3% / MVP**（≤3% 归 Q5-4）。
- `magnetostaticPathReady: true`：worker 内 `MO_FEM_DRY_RUN=0` 可 gmsh→ElmerGrid→ElmerSolver 真跑。
- 激励：简化均匀电流密度（非完整电机绕组/永磁标定）；力标量未校准。

## 文件

| 文件 | 说明 |
| --- | --- |
| `template.json` | `equationMode=magnetostatic`；`magnetostaticPathReady=true` |
| `mesh.geo` | 三层盒：coil_pm / airgap / iron + exterior BC |
| `case.sif` | **可执行** WhitneyAV 磁静力学 + SaveScalars 磁力 |

## 冒烟

```bash
# 真路径（需 Elmer；容器：docker exec mo-fem / mo-worker-fem）
python3 packages/solver-fem/smoke/run_magnetostatic_truepath.py

# 仅结构
python3 packages/solver-fem/smoke/run_magnetostatic_truepath.py --dry-run

# 旧壳占位（不调 Elmer）
python3 packages/solver-fem/smoke/run_magnetostatic_shell.py
```

边界书面：

- [Q5-2-真磁静力学后处理.md](../../../../docs/drafts/Q5-2-真磁静力学后处理.md)
- [Q4plus-5-磁静力学与轴向真值.md](../../../../docs/drafts/Q4plus-5-磁静力学与轴向真值.md)
