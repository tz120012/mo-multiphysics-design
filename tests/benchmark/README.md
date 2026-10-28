# tests/benchmark（Q2 占位）

Benchmark 用例库根目录。约定与报告模板见 [`docs/qa/Q2-Benchmark说明.md`](../../docs/qa/Q2-Benchmark说明.md)。

**本轮状态：空骨架。** 不含 MEC/ACIM 求解逻辑，无真实 golden 数值。

计划子目录（就绪后添加，当前可不存在）：

- `cases/` — 用例描述
- `golden/` — 参考输出（未校准前勿提交假精确值）
- `reports/` — 对比报告输出

勿在本目录实现求解器；对比由解析交付物驱动。
