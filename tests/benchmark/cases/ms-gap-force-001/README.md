# ms-gap-force-001 — 气隙磁拉力 FEM 验证

- **方程**：`equationMode=magnetostatic`（WhitneyAV + Maxwell），**≠ heat-proxy**
- **模板**：`packages/solver-fem/templates/ms_gap_force_3d/`
- **标杆**：教材通式 `Fz = Bg²·A/(2·μ0)`，`Bg = Br·hm/(hm+g·μr_pm)`
- **对比**：`python3 packages/solver-fem/smoke/run_fem_calibration_compare.py`
- **状态**：`pending_calibration`（Q5-4 报告结论为不可宣称 ≤3%，见标定报告）
