# Template: `ms_gap_force_3d` — 气隙磁拉力验证（Q5-4）

| 项 | 值 |
| --- | --- |
| 用途 | FEM ≤3% 标定验证几何（教材公式） |
| `equationMode` | **magnetostatic** |
| Elmer | WhitneyAV + MagnetoDynamicsCalcFields + Maxwell/nodal force |
| 几何 | 外包空气盒内：iron_return + PM + airgap + iron_target |
| 标杆 | `Fz ≈ Bg²·A/(2·μ0)`，`Bg = Br·hm/(hm+g·μr_pm)`（非饱和·忽略边缘） |

## 参数

| 符号 | 值 |
| --- | --- |
| L×W | 80×80 mm |
| hm | 8 mm |
| g | 1 mm |
| Br | 1.0 T |
| μr,iron | 1000 |
| μr,pm | 1.05 |
| 激励 | Body Force `Magnetization 3 = Br/μ0` |

**≠ heat-proxy**。Q5-4 报告结论为**不可宣称**（开放域漏磁 vs 一维假设，相对误差 ≫ 3%）；`pending_calibration` 保持。

```bash
python3 packages/solver-fem/smoke/run_fem_calibration_compare.py
```
