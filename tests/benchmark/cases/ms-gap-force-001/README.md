# ms-gap-force-001 — 闭磁路气隙磁拉力 FEM 验证

- **方程**：`equationMode=magnetostatic`（WhitneyAV + Maxwell），**≠ heat-proxy**
- **模板**：`packages/solver-fem/templates/ms_gap_force_3d/`（罐式侧轭回流）
- **标杆**：教材通式 + 书面单指标 `Fz` vs `body-rms(Bz)²·A/(2μ0)`
- **对比**：`MO_FEM_DRY_RUN=0 python3 packages/solver-fem/smoke/run_fem_calibration_compare.py`
- **状态**：见 `docs/qa/reports/标定报告-FEM-20261028-Q5-4.md`
