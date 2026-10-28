# Template: `ms_gap_force_3d` — 闭磁路气隙磁拉力验证（Q5-4）

| 项 | 值 |
| --- | --- |
| 用途 | FEM ≤3% 标定验证几何（教材公式 + 书面单指标） |
| `equationMode` | **magnetostatic** |
| Elmer | WhitneyAV + MagnetoDynamicsCalcFields + Maxwell/nodal force |
| 几何 | **罐式闭磁路**：iron_stator（底板+侧壁回流）+ PM + airgap + iron_target（盖板）；径向间隙 cr；外包空气盒 |
| 标杆 | 1D：`Fz ≈ Bg²·A/(2·μ0)`，`Bg = Br·hm/(hm+g·μr_pm)`；关闭单指标：`F = [body-rms(Bz)]²·A/(2μ0)` vs Maxwell Fz |

## 参数

| 符号 | 值 |
| --- | --- |
| 极面 L×W | 50×50 mm（A=0.0025 m²） |
| hm | 8 mm |
| g | 1 mm |
| 径向间隙 cr | 0.25 mm |
| 侧壁厚 t | 14 mm |
| 盖板高 h_lid | 25 mm |
| Br | 1.0 T |
| μr,iron | 10000 |
| μr,pm | 1.05 |
| 激励 | Body Force `Magnetization 3 = Br/μ0` |

**≠ heat-proxy**。见 `docs/qa/reports/标定报告-FEM-20261028-Q5-4.md`。

```bash
MO_FEM_DRY_RUN=0 python3 packages/solver-fem/smoke/run_fem_calibration_compare.py
```
