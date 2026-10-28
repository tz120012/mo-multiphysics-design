# Q4+-5 磁静力学 FEM 与轴向磁拉力真值路径（边界 + 壳）

| 项 | 值 |
| --- | --- |
| 状态 | **边界书面 + dry-run/真求解分界 + 可冒烟壳**（真 Elmer 磁静力学方程可为骨架） |
| 日期 | 2026-10-28（Asia/Shanghai） |
| Owner | Mo-有限元 |
| 开闸 tip | `10d3ff9`（Q4+ 基线） |
| 误差口径 | **一律 `pending_calibration`**；**禁止宣称 FEM ≤3% / MVP** |
| 对照 | [Q4plus-冒烟清单](../qa/Q4plus-冒烟清单.md) Q4+-E1 / E2；跟踪表 Q4+-5 |

> **硬分界**：`heat-proxy`（HeatEquation E2E）**≠** `magnetostatic`（磁静力学）。不得把 heat-proxy 模板原地改写成假磁静力学并宣称已通电机解。

---

## A. 三种求解模式（分界表）

| mode | 含义 | `dryRun` | Elmer 方程 | 可宣称 |
| --- | --- | --- | --- | --- |
| dry-run | 不调 Elmer；只写 thinning / manifest / 占位 scalars | `true` | 无 | **无精度**；调度/产物链可冒烟 |
| heat-proxy | Q3 E2E 调度链（`rf_pmsm_2d` / `af_pmsm_3d` 现 `case.sif`） | `false` | **HeatEquation** | **仅调度 PASS**；**≠** 电机磁解；仍 `pending_calibration` |
| magnetostatic | 磁静力学（本阶段目标路径） | `false`（真解时） | 磁矢势/标势等（**本阶段骨架/stub**） | 仍 **`pending_calibration`**；**禁 ≤3%** |

补充：

- `dryRun=true` 时无论 `equationMode` 取值，均不调用 Elmer。
- `dryRun=false` 且未显式给 `equationMode` → **兼容旧路径**，按 **heat_proxy** 解释（不得默认为磁静力学）。
- heat-proxy 成功 **不得** 填真实 `axialForceN` 冒充磁拉力。

---

## B. payload / manifest 字段建议

### B.1 payload

| 字段 | 类型 / 取值 | 说明 |
| --- | --- | --- |
| `equationMode` | `heat_proxy` \| `magnetostatic` | 缺省 + `dryRun=false` → 兼容旧路径 = `heat_proxy` |
| `templateId` | 如 `af_pmsm_3d` / `af_pmsm_3d_ms` | 磁静力学骨架推荐 `af_pmsm_3d_ms` |
| `dryRun` / 环境 `MO_FEM_DRY_RUN` | bool | 与现 Q3 runner 一致 |

### B.2 scalars（thinning / `scalars.json` / manifest 摘要）

建议键（本阶段可部分为 `null`）：

| 键 | 本阶段约定 |
| --- | --- |
| `equationMode` | `heat_proxy` \| `magnetostatic` |
| `axialForceN` / `bearingLoadN` / `deflectionHintMm` | 真值后处理未关前保持 **`null`** |
| `pending_calibration` | **恒为 `true`**（校准书面关闭前） |
| `lossesW` | 热闭环契约用；磁静力学力路径可不填损耗 |
| `magnetostaticPathReady` | 真 Elmer 磁静力学 + Maxwell/虚功后处理未关前为 **`false`** |

### B.3 真值路径（就绪后）

磁静力学收敛 → Maxwell 应力 / 虚功 → 写入 `axialForceN`（及衍生 `bearingLoadN` / `deflectionHintMm`）→ thinning 进 scalars → 专项报告引用 `resultRef`。

**未就绪前**：力标量保持 `null` + notes 标明骨架；**禁止**用 heat-proxy 温度场反推假力。

---

## C. 轴向磁拉力真值路径（步骤）

1. **几何 / 网格**：可复用 `packages/solver-fem/templates/af_pmsm_3d/` 的 Gmsh 盒网，或磁静力学骨架目录 `af_pmsm_3d_ms/`（同源 mesh 副本 + 元数据）。
2. **磁静力学 case**：`equationMode=magnetostatic`；Elmer 方程为磁矢势/标势等（本阶段 **骨架注释 + `template.json`**，非可宣称成功的假路径）。
3. **后处理 \(F_z\)**：气隙面 Maxwell 应力积分或虚功/虚位移 → `axialForceN`。
4. **thinning**：写入 `results/fem/{jobId}/scalars.json` 与 manifest 摘要；`pending_calibration: true`。
5. **专项报告**：引用 `resultRef`；口径见 [Q4-8-轴向磁拉力.md](./Q4-8-轴向磁拉力.md)（占位壳仍有效）+ 本文「真值路径」升级说明。

可冒烟壳（不依赖 Elmer 容器）：

```bash
python3 packages/solver-fem/smoke/run_magnetostatic_shell.py
python3 packages/solver-fem/smoke/run_axial_force_shell.py   # Q4-8 占位壳仍可用
```

stdout 含 `schemaVersion: magnetostatic-shell-v0`；断言 `pending_calibration`；力标量可为 `null`；`magnetostaticPathReady: false`。

---

## D. 与旧文关系

| 文档 | 关系 |
| --- | --- |
| [Q4-8-轴向磁拉力.md](./Q4-8-轴向磁拉力.md) | Q4 占位壳 + 专项报告草案 **仍有效**；本文升级「真值路径」与三种 mode 分界 |
| [Q3-F1-结果精简.md](./Q3-F1-结果精简.md) | thinning / resultRef / 禁默认全场；heat-proxy 口径不变 |
| [FEM范围.md](./FEM范围.md) | 范围笔记；Q4+-5 指针挂本文 |
| [Q3-FEM开工包.md](./Q3-FEM开工包.md) | 模板与冒烟；heat-proxy E2E 保留，磁静力学见本文 |
| [Q3-轴向与FEM边界.md](./Q3-轴向与FEM边界.md) | Q3 锁定边界不改写 |

**明确**：`rf_pmsm_2d` / `af_pmsm_3d` 的 HeatEquation **保留**；新建 `af_pmsm_3d_ms` 为磁静力学骨架，**不是**把 heat 改成磁假装已通。

---

## E. 交付物清单（本 tip）

| 交付 | 路径 |
| --- | --- |
| 本文 | `docs/drafts/Q4plus-5-磁静力学与轴向真值.md` |
| 磁静力学冒烟壳 | `packages/solver-fem/smoke/run_magnetostatic_shell.py` |
| fixture | `packages/solver-fem/fixtures/q4plus_magnetostatic_shell.json` |
| 模板骨架 | `packages/solver-fem/templates/af_pmsm_3d_ms/` |
| Q4-8 占位壳 | `smoke/run_axial_force_shell.py`（保持可用） |

---

*Mo-有限元 · Q4+-5；禁勾 ≤3%；主会话回报 Motor。*
