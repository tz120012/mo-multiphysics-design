# Q2 冒烟记录 — P05 Benchmark 框架（通过）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:38 Asia/Shanghai |
| 指派 tip | 本提交落地 cases+golden；证据 tip **`679af19`**（本提交） |
| 祖先/基线 | 阻塞记录 `6747dec` / 盘点 tip `f11a036`；compose 绿 `0ec37e2` |
| 执行 | Mo-测试执行员 |
| 性质 | Motor 正式口径复测：**框架关项**（非 ≤5% 达标宣称） |
| 主文档 | [Q2-Benchmark说明](Q2-Benchmark说明.md)、`tests/benchmark/README.md`、清单 §B |

## Motor 正式口径（本轮对齐）

| # | 交付项 | 判定规则 | 本轮 |
| --- | --- | --- | --- |
| 1 | 用例库结构 | `tests/benchmark/cases/` 至少 1–3 个径向占位 | **PASS**（3：PMSM/BLDC/ACIM） |
| 2 | 对比报告模板 | 按说明填一空报告或实跑报告 | **PASS**（SKIP 报告已填） |
| 3 | golden | `pending_calibration: true` + null；禁止假精确数 | **PASS**（3 份 pending） |
| 4 | ≤5% | **不得宣称**相对标杆达标 | **遵守**（未宣称） |
| 5 | 标杆来源 | 缺则可记「待 Mo-解析确认」 | **不挡**（README/source=pending） |
| 6 | P07 | 仅 P05 真通过后再开 | **本员未开**；条件具备回报主会话 |

## 实测盘点

```bash
cd /workspace/mo-platform
git rev-parse --short HEAD   # → 679af19（本提交）
ls tests/benchmark/cases/*/case.json
# rf-acim-smoke-001 rf-bldc-smoke-001 rf-pmsm-smoke-001
ls tests/benchmark/golden/
# rf-*-smoke-001.json ×3（pending_calibration + null）
bash scripts/smoke_q2.sh     # 占位 SKIP，exit 0
```

| 路径 | 存在？ | 说明 |
| --- | --- | --- |
| `tests/benchmark/README.md` | 是 | 状态：「已有 3 个径向占位；golden 待校准」 |
| `tests/benchmark/cases/` | **是** | 3 个径向 `case.json` + 短 README |
| `tests/benchmark/golden/` | **是** | 3 份 `pending_calibration: true`，metrics null |
| `docs/qa/reports/P05-framework-SKIP.md` | 是 | 总评 SKIP；未勾「数值有效」 |
| `scripts/smoke_q2.sh` | 是 | 恒 exit 0；**不跑比对** |

## 清单 §B 对照

| ID | 检查项 | 本轮结论 | 说明 |
| --- | --- | --- | --- |
| Q2-R1 | 用例库可枚举 | **PASS（框架）** | 3 个径向 case.json |
| Q2-R2 | golden 占位约定 | **PASS（框架）** | pending_calibration + null；无假精确数 |
| Q2-R3 | 对比报告模板 | **PASS（框架）** | SKIP 报告已填；无比对数值 |
| Q2-R4 | 误差门槛 ≤5% | **TODO / 不宣称** | 待校准 |
| Q2-R5 | 回归可重复 | **SKIP** | 无比对脚本实跑 |

## 总评

| 项 | 结论 |
| --- | --- |
| P05 | **通过（框架）** — cases×3 + golden pending + SKIP 报告；pending_calibration；**不宣称 ≤5%** |
| ≤5% | **未宣称 / 待校准** |
| 假 PASS | **无**（无编造精密 golden） |
| 开 P07 | **条件具备**（框架已过）；本员**未**开/关 P07，由主会话开 |

## 下一步

1. 主会话开 **P07**（冒烟+Motor 签字链路）。
2. Mo-解析确认标杆来源并进入校准书面化（仍不挡框架关项）。
3. 校准完成前 R4 维持 TODO；**禁止**宣称 ≤5% 达标。
