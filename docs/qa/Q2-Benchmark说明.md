# Q2 Benchmark 说明

> 对应 **Q2-5**：Benchmark 框架与首批标杆用例  
> 交付物目标：用例库 + 对比报告模板（本轮为**结构与约定占位**，不含求解逻辑与真实 golden 数值）  
> 误差目标：解析相对标杆 **≤5%（待校准）**——见 `docs/01-任务书-v2.md`；未完成校准前不得宣称达标

## 1. 目的

- 为径向解析（MEC / ACIM 等效电路等）建立可复现的**标杆对比**机制。  
- 支撑 Q2-7 解析回归与阶段验收「至少一组公开/内部标杆完成对比」。  
- **不**在本仓库由测试侧实现 MEC/ACIM 求解；对比对象为解析交付物输出 vs golden/标杆参考。

## 2. 用例库结构（约定）

仓库占位根目录：`tests/benchmark/`

```
tests/benchmark/
  README.md                 # 本结构摘要与使用约定
  .gitkeep
  cases/                    # 用例描述（就绪后新增；本轮可空）
    # <case-id>/
    #   case.json           # 元数据：机型、拓扑、输入引用、期望指标名
    #   input/              # 可选：几何快照、材料引用、求解入参
    #   README.md           # 标杆来源（公开文献 / 内部实测 / 他软件）
  golden/                   # 参考输出占位（就绪前勿提交「假精确」数值冒充已校准）
    # <case-id>.json        # 约定字段见下；可用 null + "pending_calibration": true
  reports/                  # 对比报告输出目录（gitignore 大文件可选；模板见下）
    .gitkeep
```

### case.json 最小字段（草案）

```json
{
  "id": "rf-pmsm-smoke-001",
  "topology": "radial",
  "machine": "PMSM",
  "source": "pending",
  "metrics": ["torque", "copperLoss"],
  "notes": "Q2 首批占位；标杆来源待解析侧确认"
}
```

### golden 占位约定

| 规则 | 说明 |
| --- | --- |
| 未校准 | golden 文件可缺省，或字段值为 `null` 且 `"pending_calibration": true` |
| 禁止 | 编造精密小数充当已标定 golden |
| 就绪后 | 由 Mo-解析/Mo-测试共同确认来源与容差；写入真实参考值与 `tolerance` |
| 容差默认意向 | 相对误差 ≤5%（**待校准**）；单指标可覆盖 |

示例（占位，非真实数据）：

```json
{
  "caseId": "rf-pmsm-smoke-001",
  "pending_calibration": true,
  "metrics": {
    "torque": null,
    "copperLoss": null
  },
  "toleranceRel": 0.05,
  "toleranceNote": "≤5% 待校准；正式数以标定报告为准"
}
```

## 3. 对比报告模板

建议路径（实跑后）：`tests/benchmark/reports/<tip>-<case-id>.md` 或 `docs/qa/reports/`（二选一，阶段内统一即可）。

```markdown
# Benchmark 对比报告

| 字段 | 内容 |
| --- | --- |
| 日期 | YYYY-MM-DD HH:MM Asia/Shanghai |
| tip | \`abcdef0\` |
| caseId | rf-pmsm-smoke-001 |
| 执行人 | Mo-测试 |
| 解析版本/入口 | （Wasm / API / 脚本） |

## 标杆来源

- 类型：公开 / 内部 / 他软件
- 引用：（文献或内部编号）
- 校准状态：待校准 / 已校准

## 指标对比

| 指标 | 标杆 | 本次 | 相对误差 | 门槛 | 结论 |
| --- | --- | --- | --- | --- | --- |
| torque | — | — | — | ≤5% 待校准 | SKIP |
| copperLoss | — | — | — | ≤5% 待校准 | SKIP |

## 结论

- [ ] 本组对比完成（数值有效）
- [ ] 进入校准流程 / 已书面化
- 总评：SKIP / PASS / FAIL
```

## 4. 与冒烟的关系

| 产物 | 职责 |
| --- | --- |
| [Q2-冒烟清单](Q2-冒烟清单.md) | 三种机型闭环 + 环境；日常 SKIP→实跑 |
| 本说明 + `tests/benchmark/` | 标杆用例库、golden 约定、报告模板 |
| `scripts/smoke_q2.sh` | 占位入口；当前不跑比对、exit 0 |

## 5. 首批标杆用例意向（未建文件）

| caseId（意向） | 机型 | 备注 |
| --- | --- | --- |
| `rf-bldc-smoke-001` | BLDC | 最小闭环；标杆来源 TBD |
| `rf-pmsm-smoke-001` | PMSM | 优先首组对比候选 |
| `rf-acim-smoke-001` | ACIM | 等效电路；与导条材料联动 |

本轮**不**创建上述 case 正文，避免空壳被误认为已验收。

## 6. 修订

| 日期 | 说明 |
| --- | --- |
| 2026-10-28 | Mo-测试：Q2-5 框架脚手架初稿 |
