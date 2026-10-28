# Benchmark 对比报告

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:38 Asia/Shanghai |
| tip | `679af19` |
| caseId | rf-pmsm-smoke-001 / rf-bldc-smoke-001 / rf-acim-smoke-001（三套径向占位） |
| 执行人 | Mo-测试 |
| 解析版本/入口 | （未跑数值比对）Wasm / API / 脚本均未对标 |

## 标杆来源

- 类型：待定
- 引用：待 Mo-解析确认
- 校准状态：待校准（golden `pending_calibration: true`，metrics null）

## 指标对比

| 指标 | 标杆 | 本次 | 相对误差 | 门槛 | 结论 |
| --- | --- | --- | --- | --- | --- |
| torque | — | — | — | ≤5% 待校准 | SKIP |
| copperLoss | — | — | — | ≤5% 待校准 | SKIP |

## 结论

- [ ] 本组对比完成（数值有效）
- [ ] 进入校准流程 / 已书面化
- 总评：**SKIP**（框架占位已齐；未做数值比对；**不**作 ≤5% 达标证据）
- **不得宣称**相对标杆 ≤5% 达标
