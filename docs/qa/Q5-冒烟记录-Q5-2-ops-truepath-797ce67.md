# Q5 冒烟记录 — Q5-2 运维联调（真值 tip `797ce67`）

> 执行：Mo-运维 · Asia/Shanghai  
> 对照：Mo-有限元 tip **`797ce67`**；运维支援 tip 本提交  
> **禁止**宣称 FEM ≤3% / MVP

## 步骤

1. `git` 含 `797ce67`（本机 HEAD 已祖先）
2. `docker compose … --profile fem build worker-fem`（COPY 新 `packages/solver-fem`）
3. `MO_FEM_DRY_RUN=0` recreate `mo-worker-fem`；`printenv` → **0**
4. 宿主机：`MO_FEM_DRY_RUN=0 python3 packages/solver-fem/smoke/run_magnetostatic_truepath.py`
5. 测完：`MO_FEM_DRY_RUN=1` recreate；`printenv` → **1**

## 结果

| 项 | 值 |
| --- | --- |
| runMode | `docker:mo-fem` |
| equationMode | `magnetostatic` |
| magnetostaticPathReady | `true` |
| dryRun | `false` |
| elmerExit | **0** |
| postprocess | `maxwell` |
| axialForceN | `-0.002726984380961`（占位量级；**未标定**） |
| pending_calibration | **true** |
| 结论 | **联调 PASS**（真值路径可冒烟；≠ heat-proxy；**不计 ≤3%**） |

## 口径

- heat-proxy 仍可作调度回归，**不计**本门禁。  
- 方程/Maxwell 归有限元 tip `797ce67`；运维确认镜像 + compose/dry-run 开关。
