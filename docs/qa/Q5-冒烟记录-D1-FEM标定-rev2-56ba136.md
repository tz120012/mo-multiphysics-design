# Q5 冒烟记录 — D1 rev2（FEM ≤3% 闭磁路标定复现 / Q5-4）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 18:52 Asia/Shanghai |
| 业务 tip | **`56ba136`**（`feat(fem): Q5-4 closed pot-core gap-force; single-metric ≤3%`） |
| tip 全 SHA | `56ba136dfa7a92e7e57da1182cd221312a38af5e` |
| 报告 | [标定报告-FEM-20261028-Q5-4](reports/标定报告-FEM-20261028-Q5-4.md)（**rev2**） |
| 祖先确认 | `git merge-base --is-ancestor 56ba136 HEAD` → **0**（HEAD=`56ba136`） |
| 实测 tip（写记录时 HEAD） | **`56ba136`** |
| 执行 | Mo-测试；**仅** `docs/qa/` 证据入库；**未**改业务代码；**未** push |
| 性质 | Motor 正式复现令 · Q5-4 rev2；按报告 §3.2 实跑；总评 **SKIP（复现通过·单指标可宣称·禁勾 F2）**；**勿勾 F2**；**不开 MVP**；**不代签** |
| rev1 对照 | tip **`76dc43a`** / 证据 [D1-76dc43a](Q5-冒烟记录-D1-FEM标定-76dc43a.md)（开放域 rel≈93%；**不作**关闭依据）；另历史 tip **`bb3dfcb`** 同族开放域证据亦**不作**关闭依据 |

## 环境

| 证据 | 结果 |
| --- | --- |
| tip 类型 | `git cat-file -t 56ba136` → **commit** |
| 祖先 | `56ba136` = HEAD |
| Elmer | `docker:mo-fem`（容器 Up） |
| Python | `python3`（系统） |
| 工作目录 | `/workspace/mo-platform` |
| 隔离 | 仅 mo-platform；本轮**未**改 `apps/`/`packages/`；heat-proxy **不计入** |

## 复现命令与实测（对照报告 §3.2）

```bash
MO_FEM_DRY_RUN=0 python3 packages/solver-fem/smoke/run_fem_calibration_compare.py
```

容差：与报告表列量级一致（有效数字 / 相对误差量级）。实跑耗时约 47 s；exit **0**。

### 标定对比（`ms-gap-force-001` / `ms_gap_force_3d` · 罐式闭磁路）

| 项 | 报告期望（rev2） | 实测 | 比对 |
| --- | --- | --- | --- |
| exit | 0 | **0** | 一致 |
| runMode | `docker:mo-fem` | **docker:mo-fem** | 一致 |
| equationMode | magnetostatic | **magnetostatic** | 一致 |
| elmerExit | 0 | **0** | 一致 |
| templateId | `ms_gap_force_3d` | **ms_gap_force_3d** | 一致 |
| axialForceN（FEM） | ≈-712.5611940496 N（\|F\|≈712.56） | **-712.5611940496** N | **一致** |
| magneticEnergyJ | ≈7.355455663579 J | **7.355455663579** J | **一致** |
| Bg body-mean（气隙） | ≈0.8263688761075 T | **0.8263688761075** T | **一致** |
| Bg body-rms（气隙） | ≈0.8408564269354 T | **0.8408564269354** T | **一致** |
| Fz_from_Bg（body-rms） | ≈703.3052 N | **703.3052267202127** N | 一致 |
| 单指标 relError | ≈0.0132（1.32%） | **0.013160669049128944** | **量级一致** |
| within_3pct（单指标） | true | **true** | 一致 |
| claimable_fem_le_3pct | true | **true** | 一致 |
| claimScope | 仅本 case / 本模板 | 仅 verification case ms-gap-force-001 / 本模板；非完整 AF 电机；heat-proxy 不计 | 一致 |
| compare_1d relError | ≈0.0833（8.33%，对照） | **0.08327473118522241** | 量级一致；**不作**关闭依据 |
| pending_calibration | false（按本范围关闭意向） | **false** | 一致 |
| heatProxyCounted | false | **false** | 一致 |
| postprocess | maxwell | **maxwell** | 一致 |
| ≠ heat-proxy | 是 | equationMode=magnetostatic；heatProxyCounted=false | 一致 |

关键 JSON 字段摘录（stdout）：

```
"equationMode": "magnetostatic",
"elmerExit": 0,
"templateId": "ms_gap_force_3d",
"axialForceN": -712.5611940496,
"Bg_fem_body_rms_T": 0.8408564269354,
"compare_single_metric_Bg.relError": 0.013160669049128944,
"claimable_fem_le_3pct": true,
"heatProxyCounted": false
```

## 总评

| 项 | 结论 |
| --- | --- |
| 复现 vs 报告量级 | **一致**（闭磁路 \|Fz\|≈712.56 N；Bg body-rms≈0.8409 T；单指标 rel≈**1.32%**） |
| equationMode / elmerExit | magnetostatic / 0 |
| 几何 | 罐式闭磁路（≠ rev1 开放域） |
| pending_calibration | **false**（按本 case 单指标范围关闭意向；与报告一致） |
| ≠ heat-proxy | **是** |
| ≤3% / 可宣称 | **同意报告口径**：可宣称 FEM ≤3%（**仅** `ms-gap-force-001` / 模板 `ms_gap_force_3d` / 书面单指标 body-rms(Bz)）；**不可**外推整机 / AF 电机 |
| 1D 对照 / rev1 | 1D≈8.33% **未**作关闭；rev1≈93% / tip `bb3dfcb`·`76dc43a` **不作**关闭依据 |
| F2 | **禁勾**（须本复现 + **Motor 书面签字**；本员**未勾**） |
| 清单 D1 记法 | **SKIP（复现通过·单指标可宣称·禁勾 F2）** |
| MVP / tag | **未宣称**；**未**代签 |

> 本记录为 Q5-4 **rev2 正式复现证据**。数值与报告 §3.2 / §4.2 一致；**同意**有限范围可宣称。**禁止**勾选 Q5-F2 / Q4+-F2，直至 Motor 书面签字；**禁止**开 MVP；**禁止**把结论外推到 `af_pmsm_3d_ms` 或整机。

## 未做

- 未改 `packages/` / `apps/` / golden 数值
- **未勾** F1/F2；未代签；未宣称 MVP；未打 tag
- 未把产品跟踪 Q5-4 行改为「通过」（仅测试注记；关闭勾选交 Motor）

---

*Mo-测试 · Q5-4 / D1 rev2 · tip `56ba136` · 单指标 ≈1.32% · 禁勾 F2 · 不开 MVP。*
