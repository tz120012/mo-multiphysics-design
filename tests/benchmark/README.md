# tests/benchmark（Q2 占位）

Benchmark 用例库根目录。约定与报告模板见 [`docs/qa/Q2-Benchmark说明.md`](../../docs/qa/Q2-Benchmark说明.md)。

**本轮状态：已有 3 个径向占位；golden 待校准。** 不含 MEC/ACIM 求解逻辑，无真实 golden 数值（`pending_calibration: true` + metrics null）。**不得宣称**相对标杆 ≤5% 达标。

子目录：

- `cases/` — 用例描述（`rf-pmsm-smoke-001` / `rf-bldc-smoke-001` / `rf-acim-smoke-001`）
- `golden/` — 参考输出占位（pending；禁止假精确数）
- `reports/` — 对比报告输出

勿在本目录实现求解器；对比由解析交付物驱动。
Q3 FEM 用例（heat-proxy 指针）见 [`docs/qa/Q3-FEM-Benchmark说明.md`](../../docs/qa/Q3-FEM-Benchmark说明.md)（`rf-pmsm-fem-heat-proxy-001` / `af-pmsm-fem-heat-proxy-001`；`pending_calibration`；**不得宣称** ≤3%/≤5%）。勿改坏 Q2 径向 cases。

