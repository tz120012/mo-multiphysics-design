# Q2 冒烟记录 — P05 Benchmark 框架 @ `f11a036`

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:36 Asia/Shanghai |
| 指派 tip | **无新业务 tip**（Motor：按现文档判定）；证据 HEAD **`f11a036`** |
| 祖先/基线 | compose 绿 tip `0ec37e2` / docs `0d7d923`；Wasm UI `5faa977`/`cd8ae87` 已关 |
| 执行 | Mo-测试执行员 |
| 性质 | Motor 正式开 P05；**框架关项**（非 ≤5% 达标宣称） |
| 主文档 | [Q2-Benchmark说明](Q2-Benchmark说明.md)、`tests/benchmark/README.md`、清单 §B |

## Motor 正式口径（本轮对齐）

| # | 交付项 | 判定规则 |
| --- | --- | --- |
| 1 | 用例库结构 | `tests/benchmark/cases/` 至少 1–3 个径向占位（PMSM/BLDC/ACIM） |
| 2 | 对比报告模板 | 按说明填一空报告或实跑报告 |
| 3 | golden | 未校准可用 `pending_calibration: true` + null；**禁止假精确数** |
| 4 | ≤5% | **不得宣称**相对标杆达标（任务书：待校准） |
| 5 | 标杆来源 | 缺则可记「待 Mo-解析确认」；**不挡框架关项** |
| 6 | P07 | **仅 P05 真通过后再开** |

## 实测盘点（只读，未改业务/tests）

```bash
cd /workspace/mo-platform
git rev-parse --short HEAD   # → f11a036
ls -la tests/benchmark/
# README.md + .gitkeep + reports/.gitkeep
# 无 cases/；无 golden/
bash scripts/smoke_q2.sh     # 占位 SKIP，exit 0
```

| 路径 | 存在？ | 说明 |
| --- | --- | --- |
| `tests/benchmark/README.md` | 是 | 自述「空骨架；无真实 golden」 |
| `tests/benchmark/reports/` | 是 | 仅 `.gitkeep` |
| `tests/benchmark/cases/` | **否** | 意向 caseId（`rf-*-smoke-001`）说明里写明「本轮不创建正文」 |
| `tests/benchmark/golden/` | **否** | 无 `pending_calibration` 占位文件 |
| `docs/qa/Q2-Benchmark说明.md` | 是 | 结构约定 + 报告模板 + golden 规则已落盘 |
| `scripts/smoke_q2.sh` | 是 | 恒 exit 0；**不跑比对** |

## 清单 §B 对照

| ID | 检查项 | 本轮结论 | 说明 |
| --- | --- | --- | --- |
| Q2-R1 | 用例库可枚举 | **阻塞** | `cases/` 目录不存在；0 个 case.json |
| Q2-R2 | golden 占位约定 | **部分** | 文档约定已有；`golden/` 文件未建（可用 pending null，但目录/文件仍缺） |
| Q2-R3 | 对比报告模板 | **部分 PASS** | 模板在说明 §3；本轮填空报告见 [reports/P05-empty-f11a036](reports/P05-empty-f11a036.md)（无数值比对） |
| Q2-R4 | 误差门槛 ≤5% | **TODO / 不宣称** | 待校准；本轮**不**宣称达标 |
| Q2-R5 | 回归可重复 | **SKIP** | 无比对脚本/用例可跑 |

## 缺什么 / 谁该交

| 缺口 | 责任方（建议） | 备注 |
| --- | --- | --- |
| `tests/benchmark/cases/{rf-pmsm,rf-bldc,rf-acim}-smoke-001/case.json`（至少 1，意向 3） | **Mo-测试**（Q2-5 共责）落地结构；标杆字段由 **Mo-解析** 确认来源 | 本执行员隔离 **仅可改 `docs/qa/`**，无法提交 `tests/benchmark/cases/` |
| `tests/benchmark/golden/<case-id>.json`（`pending_calibration: true`，metrics null） | Mo-测试 | **禁止**编造精密小数 |
| （可选）`scripts/smoke_q2.sh` 枚举 cases 而不做假 PASS | Mo-测试 | 仍须避免主 CI 硬挂 |
| 标杆来源 / 校准计划正文 | Mo-解析 + Mo-测试 | 来源「待确认」**不挡**框架关项；校准书面化属阶段出口 |

## 总评

| 项 | 结论 |
| --- | --- |
| P05 | **阻塞**（框架交付未齐：缺 `cases/` 至少 1 个用例描述；`golden/` 未建） |
| ≤5% | **未宣称 / 待校准** |
| 假 PASS | **无** |
| 开 P07 | **不具备条件**（须 P05 真通过） |

## 下一步

1. Mo-测试（或有权改 `tests/benchmark/` 的执行员）按 [Q2-Benchmark说明](Q2-Benchmark说明.md) 落下 1–3 个径向 `cases/` + pending `golden/`。
2. Mo-解析确认标杆来源（可先写「待确认」）。
3. 复测 R1–R3 → 框架可标 **通过**（仍不宣称 ≤5%）。
4. 其后才开 **P07**。
