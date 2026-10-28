# 解析 vs FEM 对照报告（空模板）

> 用途：Q3-P07 / Q3-F3 可填骨架。口径：**heat-proxy** / `pending_calibration`。  
> **禁止**勾选「可宣称 ≤3%/≤5%」直至校准书面关闭。**不填假数**。  
> 说明见 [Q3-FEM-Benchmark说明](../Q3-FEM-Benchmark说明.md)。

| 字段 | 内容 |
| --- | --- |
| 日期 | YYYY-MM-DD HH:MM Asia/Shanghai |
| tip | `` |
| caseId | rf-pmsm-fem-heat-proxy-001 / af-pmsm-fem-heat-proxy-001（或 RF-PMSM-2D / AF-PMSM-3D heat-proxy） |
| 执行人 | Mo-测试 |
| 解析入口 | （Wasm / API / CLI） |
| FEM 入口 | （Jobs / Elmer；默认注明 heat-proxy） |
| 校准状态 | **pending_calibration** |
| 证据指针（可选） | tip `291bea9` / `2c1fed6`（+`781c09b`）；见 [L2 Elmer E2E](../Q3-冒烟记录-L2-elmer-e2e-2c1fed6.md) |

## 标杆 / 对照说明

- 类型：解析输出 vs FEM 输出（本轮可为 heat-proxy 调度证据指针，非磁静力学）
- 引用：（文献或内部编号；未定则留空）
- 校准状态：待校准 / 已校准（默认：**待校准**）

## 指标对比

| 指标 | 解析 | FEM | 相对差 | 门槛 | 结论 |
| --- | --- | --- | --- | --- | --- |
| （待填） | — | — | — | ≤3% 待校准 | SKIP |
| （待填） | — | — | — | ≤5% 待校准（解析侧） | SKIP |

## 结论

- [ ] 本组对照完成（数值有效）
- [ ] 进入校准流程 / 已书面化
- [ ] 可宣称 FEM ≤3%（**禁止**在校准关闭前勾选）
- [ ] 可宣称解析 ≤5%（**禁止**在校准关闭前勾选）
- 总评：**SKIP**（空模板；无假数；**不**作 ≤3%/≤5% 达标证据）
