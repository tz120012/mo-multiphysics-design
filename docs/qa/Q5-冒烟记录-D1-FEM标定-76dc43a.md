# Q5 冒烟记录 — D1（FEM ≤3% 标定复现 / Q5-4）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 18:37 Asia/Shanghai |
| 业务 tip | **`76dc43a`**（`docs(fem): Q5-4 FEM magnetostatic calibration report`） |
| tip 全 SHA | `76dc43a524a20fb19e41b3f7c58c527c335b9144` |
| 报告 | [标定报告-FEM-20261028-Q5-4](reports/标定报告-FEM-20261028-Q5-4.md) |
| 祖先确认 | `git merge-base --is-ancestor 76dc43a HEAD` → **0** |
| 实测 tip（写记录时 HEAD） | **`24fb04b`**（产品记 Q5-4 阻塞之上；FEM 脚本/模板自 `76dc43a` 起无后续业务改动影响本复现） |
| 执行 | Mo-测试；**仅** `docs/qa/` 证据入库；**未**改业务代码；**未** push |
| 性质 | Motor 交测 Q5-4；按报告 §3 **复现抽测**量级；总评 **SKIP（复现通过·禁勾 F2）**；**勿勾 F2**；**不代判关闭 / 不宣称 ≤3%/MVP** |

## 环境

| 证据 | 结果 |
| --- | --- |
| tip 类型 | `git cat-file -t 76dc43a` → **commit** |
| 祖先 | `76dc43a` 为 HEAD 祖先 |
| Elmer | `docker:mo-fem`（`sudo docker`；容器 Up） |
| Python | `python3`（系统） |
| 工作目录 | `/workspace/mo-platform` |
| 隔离 | 仅 mo-platform；本轮**未**改 `apps/`/`packages/`；heat-proxy **不计入**本门槛 |

## 复现命令与实测（对照报告 §3）

容差：与报告表列量级一致（报告给出的有效数字 / 相对误差量级）。

### 1. 真值路径冒烟（`af_pmsm_3d_ms`，非本标杆几何）

```bash
MO_FEM_DRY_RUN=0 python3 packages/solver-fem/smoke/run_magnetostatic_truepath.py
```

| 项 | 报告期望 | 实测 | 比对 |
| --- | --- | --- | --- |
| exit | 0 | **0** | 一致 |
| runMode | `docker:mo-fem` | **docker:mo-fem** | 一致 |
| equationMode | magnetostatic | **magnetostatic** | 一致 |
| elmerExit | 0 | **0** | 一致 |
| axialForceN | ≈-0.002726984380961 N | **-0.002726984380961** N | **一致** |
| magneticEnergyJ | ≈9.236521314775e-05 J | **9.236521314775e-05** J | **一致** |
| postprocess | maxwell | **maxwell** | 一致 |
| pending_calibration | true | **true** | 一致 |
| ≠ heat-proxy | 是（WhitneyAV / notes） | notes 明示 ≠ heat-proxy；templateId=`af_pmsm_3d_ms` | 一致 |

关键 stdout：

```
Q5-2 magnetostatic truepath smoke OK (runMode=docker:mo-fem; axialForceN=-0.002726984380961; pending_calibration)
```

### 2. 标定对比（`ms-gap-force-001` / `ms_gap_force_3d`）

```bash
MO_FEM_DRY_RUN=0 python3 packages/solver-fem/smoke/run_fem_calibration_compare.py
```

| 项 | 报告期望 | 实测 | 比对 |
| --- | --- | --- | --- |
| exit | 0（跑通；是否 ≤3% 见 claimable） | **0** | 一致 |
| runMode | `docker:mo-fem` | **docker:mo-fem** | 一致 |
| equationMode | magnetostatic | **magnetostatic** | 一致 |
| elmerExit | 0 | **0** | 一致 |
| templateId | `ms_gap_force_3d` | **ms_gap_force_3d** | 一致 |
| axialForceN（FEM） | ≈-132.3944655091 N（\|F\|≈132.39） | **-132.3944655091** N | **一致** |
| magneticEnergyJ | ≈5.104730133369 J | **5.104730133369** J | **一致** |
| Bg body-mean | ≈0.1673755088066 T | **0.1673755088066** T | **一致** |
| Fz_ref（教材） | ≈1989.8619 N | **1989.8618690040087** N | 一致 |
| relError（主对比） | ≈0.9335（93.35%） | **0.9334654995045623** | **量级一致** |
| within_3pct / claimable | false | **false** / `claimable_fem_le_3pct=false` | 一致 |
| pending_calibration | true | **true**（stdout + golden） | 一致 |
| heatProxyCounted | false / 不计 | **false** | 一致 |
| ≠ heat-proxy | 是 | equationMode=magnetostatic；heatProxyCounted=false | 一致 |

备选单指标（报告 §4.2）：`relError≈0.8559`（85.59%）；实测 **0.8558629251204063** — 量级一致；**不**作关闭依据。

## 总评

| 项 | 结论 |
| --- | --- |
| 复现 vs 报告量级 | **一致**（真路径力/能量；标定 \|Fz\|、能量、Bg、相对误差 ≈93%） |
| equationMode / elmerExit | magnetostatic / 0 |
| pending_calibration | **true**（保持；未翻转） |
| ≠ heat-proxy | **是** |
| ≤3% / 可宣称 | **否**（与报告「不可宣称」一致；本员**不代判关闭**） |
| F2 | **禁勾**（对照报告 §7 / §9；本员**未勾**） |
| 清单 D1 记法 | **SKIP（复现通过·禁勾 F2）** |
| MVP / tag | **未宣称**；**未**代签 |

> 本记录仅为 Q5-4 **复现抽测证据**。报告结论为草稿/阻塞（数值未达 ≤3%）；**禁止**勾选 Q5-F2 / Q4+-F2；**禁止**宣称 FEM ≤3% 或 MVP。

## 未做

- 未改 `packages/` / `apps/` / golden 数值或 `pending_calibration`
- 未代判产品 Q5-4「通过」或数值关闭
- 未勾 F1/F2；未宣称 ≤3%/MVP；未打 tag

---

*Mo-测试 · Q5-4 / D1 · 隔离仅 `/workspace/mo-platform` · 禁勾 F2。*
