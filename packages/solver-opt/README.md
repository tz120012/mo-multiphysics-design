# packages/solver-opt — NSGA-II 多目标优化（Q4-9）

| 项 | 值 |
| --- | --- |
| Owner | **Mo-解析** |
| 状态 | Q4-9 骨架（Motor F3/F4 已拍；见边界稿） |
| MVP | **analytic-only** 适应度；`jobType=optimize` **异步**（本包不实现 Celery/API） |
| 精度 | **不宣称** 误差门禁 / ≤5% |

边界锁定：[`docs/drafts/Q4-NSGA-II跨服务边界.md`](../../docs/drafts/Q4-NSGA-II跨服务边界.md)（包名 **`solver-opt`**；**禁止**把 NSGA 塞进 `packages/solver-analytic` 根）。

## Jobs

- 外层仅 `jobType=optimize`（异步 Jobs；由 Mo-后端入队）。
- 本包提供：payload / manifest / pareto **JSON Schema**、analytic 目标适配器、固定 seed fixture、极简 NSGA 占位入口。
- **不做**：Celery worker、FastAPI 长跑、全种群 FEM。

## 目录

```
packages/solver-opt/
  README.md
  api/                 # OptimizeJobPayload / OptimizeManifest / ParetoResults
  nsga/                # 极简纯 Python 占位（无 pymoo/scipy 硬依赖）
  adapters/            # analytic 目标适配器 → solver-analytic.solve
  fixtures/            # 固定 seed 可复现样例 + 预计算帕累托摘要
  smoke/run_opt_seed.py
```

## MVP 目标（analytic-only）

RF+PMSM，调用 `packages/solver-analytic.solve`（默认 `solver=mec`）：

| metricId | sense | 公式（解析出口） |
| --- | --- | --- |
| `abs_torque` | maximize | `|torque_nm|` |
| `copper_iron_loss` | minimize | `losses_w.copper + losses_w.iron` |

变量 knobs（fixture）：`magnet_thickness_m`、`turns_per_phase`。约束写在 fixture payload。

## 依赖

- **默认路径**：纯 Python 3；仅 import 同仓 `solver-analytic`。
- **可选**：pymoo / scipy — **非硬依赖**；fixture / stub 默认无强依赖。选型进 worker 镜像后置（边界 L5）。

## 冒烟

```bash
python3 packages/solver-opt/smoke/run_opt_seed.py
```

期望：exit 0；打印 `seed`、代数、帕累托点数；同 seed 摘要确定性。

## Stretch（非门禁）

- 完整 NSGA-II（或 pymoo）进 worker 镜像
- `analytic+drive` 目标适配
- 精英个体 spot FEM hook（`adapters/fem_spot_hook.py`）
- Celery optimize worker（Mo-后端 / 运维）

## 不做

- 不改 `apps/api` / Celery
- 不强制宿主机 scipy/pymoo
- 不挡 Q4-6/7；不大改 `solver-analytic`（只调用）
