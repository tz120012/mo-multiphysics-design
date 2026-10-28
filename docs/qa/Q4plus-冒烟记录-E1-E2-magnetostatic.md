# Q4+ 冒烟记录 — E1/E2（磁静力学边界 + CLI shell）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 15:27 Asia/Shanghai |
| FEM tip | **`9ffa4b2`**（`feat(fem): Q4+-5 magnetostatic boundary + axial true-path shell`） |
| 仓库 HEAD（实测时） | **`1019d1a`**（`9ffa4b2` 为祖先；`git merge-base --is-ancestor 9ffa4b2 HEAD` → 0） |
| 执行 | Mo-测试 |
| 范围 | **仅** Q4+-E1 / Q4+-E2；对照边界稿与 magnetostatic shell；**不**勾 F1/F2；**不**代签；**不开宣称 MVP** |

## 环境

- 工作目录：`/workspace/mo-platform`。
- FEM 交测 tip **`9ffa4b2`** 已在历史中。
- 冒烟命令：`MO_FEM_DRY_RUN=1 python3 packages/solver-fem/smoke/run_magnetostatic_shell.py`（脚本本身 dry-run，不调 Elmer）。
- 未改 `packages/` / `apps/` 业务代码；本 commit **仅** `docs/qa` 中 E1/E2 / Q4+-5 相关证据。

## E1 — dry-run / 真求解边界文档

| 检查 | 结果 | 依据 |
| --- | --- | --- |
| 边界稿存在且可指向 | **PASS** | [docs/drafts/Q4plus-5-磁静力学与轴向真值.md](../drafts/Q4plus-5-磁静力学与轴向真值.md)（tip `9ffa4b2` 引入） |
| 书面写明 heat-proxy ≠ 磁静力学 | **PASS** | 文首硬分界：`heat-proxy`（HeatEquation E2E）**≠** `magnetostatic`；不得把 heat-proxy 改写成假磁静力学并宣称已通电机解 |
| dry-run / 真求解分界 | **PASS** | §A 三种 mode 表：`dry-run` / `heat-proxy` / `magnetostatic`；`dryRun=true` 不调 Elmer；缺省 + `dryRun=false` → 兼容旧路径 = heat_proxy（不得默认为磁静力学） |
| 禁勾 ≤3% / pending_calibration | **PASS** | 误差口径一律 `pending_calibration`；**禁止宣称 FEM ≤3% / MVP**；§B 力标量未关前保持 **null** |

**heat-proxy ≠ 磁静力学依据（摘录要点，非全引）：**

1. 文首硬分界句：heat-proxy ≠ magnetostatic；禁止假改写宣称。
2. §A：heat-proxy 仅调度 PASS，≠ 电机磁解；magnetostatic 本阶段骨架/stub，仍 pending_calibration，禁 ≤3%。
3. §D：`rf_pmsm_2d` / `af_pmsm_3d` HeatEquation **保留**；新建 `af_pmsm_3d_ms` 为磁静力学骨架，**不是**把 heat 改成磁假装已通。

**E1 结论：PASS**（边界书面化；tip `9ffa4b2`）。

## E2 — 可冒烟壳升级

| 检查 | 结果 | 依据 |
| --- | --- | --- |
| 命令可跑 | **PASS** | `MO_FEM_DRY_RUN=1 python3 packages/solver-fem/smoke/run_magnetostatic_shell.py` |
| exit code | **PASS** | **0** |
| `pending_calibration` | **PASS** | stdout / scalars 均为 `true` |
| 力标量 null（未标定） | **PASS** | `axialForceN` / `bearingLoadN` / `deflectionHintMm` 均为 **null**；`magnetostaticPathReady: false` |
| 禁勾 ≤3% | **PASS** | notes 含 `do NOT claim FEM ≤3%`；清单 F2 **未勾** |
| heat-proxy 模板未改写 | **PASS** | 脚本断言 `af_pmsm_3d/case.sif` 仍含 HeatEquation |

### stdout 要点（实测）

```json
{
  "schemaVersion": "magnetostatic-shell-v0",
  "equationMode": "magnetostatic",
  "pending_calibration": true,
  "magnetostaticPathReady": false,
  "reportDraft": "docs/drafts/Q4plus-5-磁静力学与轴向真值.md",
  "scalars": {
    "axialForceN": null,
    "bearingLoadN": null,
    "deflectionHintMm": null,
    "pending_calibration": true,
    "dryRun": true,
    "templateId": "af_pmsm_3d_ms"
  },
  "notes": "magnetostatic true-path shell; heat-proxy ≠ magnetostatic; Maxwell/virtual-work not closed; do NOT claim FEM ≤3%"
}
```

stderr：`Q4+-5 magnetostatic shell smoke OK (pending_calibration; path not ready)`

**E2 结论：PASS**（CLI shell；禁勾 ≤3%；力标量未标定 null）。

## 未做 / 禁止宣称

- **未**勾选 Q4+-F1 / Q4+-F2。
- **未**代签数值门禁；**未**宣称真 Elmer 磁静力学 / Maxwell 后处理已关。
- **未**开宣称 MVP 已达成。
- **未**改业务代码；本 commit **仅** E1/E2 / Q4+-5 docs。
- 本记录仅关 Q4+-5 的 **CLI shell / 边界文档** 口径；真值路径仍骨架。

## 跟踪 / 清单变更

| 项 | 变更 |
| --- | --- |
| [Q4plus-验收跟踪](Q4plus-验收跟踪.md) | Q4+-5 → **通过（CLI shell / 边界文档）**；备注 E1/E2 PASS；**仍禁勾 ≤3%** |
| [Q4plus-冒烟清单](Q4plus-冒烟清单.md) | Q4+-E1 / Q4+-E2 → **PASS**（注明 tip `9ffa4b2`）；F1/F2 **不勾** |
| Q4+-6 | 仍未全开；注明「E1/E2 已补记录」 |

## 结论

| ID | 结论 |
| --- | --- |
| Q4+-E1 | **PASS** |
| Q4+-E2 | **PASS** |
| Q4+-5 | **通过（CLI shell / 边界文档）**（**产品已确认**） |
| Q4+-F1 / F2 | **禁止勾选** |
| MVP | **不开宣称** |

证据 tip：本记录入库 commit 的 short SHA；交测对照 FEM tip **`9ffa4b2`**；冒烟入库 tip **`0685e96`**。

**产品确认（Mo-产品）**：同意 E1/E2 PASS → Q4+-5 **通过（CLI shell / 边界文档）**；heat-proxy≠磁静力学；shell `pending_calibration`；力标量 null；**禁勾 ≤3%**；真 Elmer/Maxwell 后处理仍后置；**不开宣称 MVP**。

---

*Mo-测试 · Q4+-E1/E2 · 隔离仅 `/workspace/mo-platform`。*
