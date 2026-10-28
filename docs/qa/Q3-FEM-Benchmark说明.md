# Q3 FEM Benchmark 说明

> 对应 **Q3-7 / P07**：FEM Benchmark 框架与「解析 vs FEM」对照机制  
> 交付物目标：用例枚举 + 对照报告模板（本轮为**结构占位**，**非**数值验收）  
> 口径：`pending_calibration`；误差意向 FEM 相对标杆 **≤3%（待校准）** / 解析 **≤5%（待校准）**——见 `docs/01-任务书-v2.md`  
> **禁止**：未完成校准书面关闭前宣称 FEM ≤3% / 解析 ≤5% 达标；**禁止**勾选冒烟清单 F4/F5

## 1. 目的

- 为 Q3 FEM 建立可复现的 **「解析 vs FEM」对照** 机制与用例枚举入口。  
- 对齐 [Q2-Benchmark说明](Q2-Benchmark说明.md) 风格；径向解析 cases 已在 `tests/benchmark/`，本轮 **扩展指针**，不破坏 Q2 用例。  
- **本轮仅为结构占位**：指向已有 heat-proxy E2E 证据；**不**编造精密 golden；**不**代签；**不**开 Q4。

## 2. 口径（强制）

| 规则 | 说明 |
| --- | --- |
| 校准状态 | 一律 `pending_calibration`（直至书面关闭） |
| 禁止宣称 | **不得**宣称 FEM ≤3% / 解析 ≤5% 达标 |
| 禁止勾选 | 冒烟清单 **Q3-F4 / Q3-F5** 在校准关闭前保持「禁止勾选」 |
| heat-proxy | 现有 E2E 为 Elmer **heat-proxy 调度链**，**非**磁静力学电机解；不得当作数值校核通过 |
| golden | 可缺省；若建占位须 `pending_calibration: true` + metrics `null`；**禁止**假精确数 |

## 3. 用例库约定

仓库根：`tests/benchmark/`（与 Q2 共用；可扩展）

```
tests/benchmark/
  README.md
  cases/
    rf-*-smoke-001/          # Q2 径向解析占位（保留）
    rf-pmsm-fem-heat-proxy-001/   # Q3 FEM 指针（本轮可选落地）
    af-pmsm-fem-heat-proxy-001/   # Q3 FEM 指针（本轮可选落地）
  golden/                    # 未校准勿提交假精密数；可用 null + pending_calibration
  reports/
```

### case.json 最小字段（FEM 指针草案）

```json
{
  "id": "rf-pmsm-fem-heat-proxy-001",
  "topology": "radial",
  "machine": "PMSM",
  "dim": "2d",
  "kind": "fem-heat-proxy",
  "source": "docs/qa/Q3-冒烟记录-L2-elmer-e2e-2c1fed6.md#tips-291bea9-2c1fed6-781c09b",
  "metrics": [],
  "notes": "Q3 FEM 指针；非磁静力学；pending_calibration；勿宣称 ≤3%"
}
```

FEM 用例也可用**本文档指针**代替仓库内假 golden；数值验收另轮。

## 4. 首批 FEM 用例枚举（heat-proxy 证据指针）

| caseId / 标签 | 拓扑·机型 | 证据 | job 示例 | 备注 |
| --- | --- | --- | --- | --- |
| **RF-PMSM-2D** heat-proxy | RF / PMSM / 2D | 冒烟 tip **`291bea9`**；业务 tip **`2c1fed6`**（+ 后端 **`781c09b`**） | `17d711f6-48ac-4afb-9632-85f45b365f2d` | `dryRun=false` / `elmerExit=0`；**非**磁静力学；见 [L2 Elmer E2E](Q3-冒烟记录-L2-elmer-e2e-2c1fed6.md) |
| **AF-PMSM-3D** heat-proxy | AF / PMSM / 3D | 同上证据 tip | `98279d72-f196-4307-9572-b456ad8f13ce` | 同上；完整 id 见 L2 冒烟记录 |

> 上表**仅枚举与指针**，不构成 ≤3%/≤5% 数值验收。框架占位 ≠ 数值验收。

## 5. 「解析 vs FEM」对照报告模板

空模板落盘：[Q3-解析vsFEM-对照报告模板](reports/Q3-解析vsFEM-对照报告模板.md)  
（亦可复制下方骨架到 `docs/qa/reports/` 实跑文件。）

```markdown
# 解析 vs FEM 对照报告（模板）

| 字段 | 内容 |
| --- | --- |
| 日期 | YYYY-MM-DD HH:MM Asia/Shanghai |
| tip | \`abcdef0\` |
| caseId | rf-pmsm-fem-heat-proxy-001 / af-pmsm-fem-heat-proxy-001 |
| 执行人 | Mo-测试 |
| 解析入口 | （Wasm / API / CLI） |
| FEM 入口 | （Jobs / Elmer；注明 heat-proxy 或否） |
| 校准状态 | pending_calibration |

## 标杆 / 对照说明

- 类型：解析输出 vs FEM 输出（本轮 heat-proxy 仅调度证据）
- 引用：（文献或内部编号；未定则留空）
- 校准状态：待校准 / 已校准

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
- 总评：SKIP / PASS / FAIL（默认 **SKIP**；本模板不填假数）
```

## 6. 与冒烟 / 验收的关系

| 产物 | 职责 |
| --- | --- |
| [Q3-冒烟清单](Q3-冒烟清单.md) **E 区** | F1–F3 骨架；F4/F5 禁止勾选；F6/F7 heat-proxy 口径 |
| [Q3-验收跟踪](Q3-验收跟踪.md) **P07** | 进行中；骨架开；未代签；未开 Q4 |
| [Q3-冒烟记录-L2-elmer-e2e-2c1fed6](Q3-冒烟记录-L2-elmer-e2e-2c1fed6.md) | RF/AF heat-proxy E2E 证据（`291bea9` / `2c1fed6`） |
| 本说明 + 对照模板 | 用例枚举、pending_calibration、报告骨架 |

## 7. 修订

| 日期 | 说明 |
| --- | --- |
| 2026-10-28 | Mo-测试：Q3-P07 FEM Benchmark 骨架（F1–F3）；指针 RF/AF heat-proxy；**未**宣称 ≤3%/≤5% |
