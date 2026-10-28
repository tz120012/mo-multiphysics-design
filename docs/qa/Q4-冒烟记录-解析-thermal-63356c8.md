# Q4 冒烟记录 — 解析 thermal tip `63356c8`（叠 `dd94137`；Q4-P06 / Q4-P07）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:27 Asia/Shanghai |
| 指派 tip | **`63356c8`**（`feat(solver): LPTN thermal loop MVP + smoke`）；叠 **`dd94137`**（`feat(solver): demag margin + ACIM bar rise MVP`） |
| 仓库 HEAD（实测时） | 冒烟时链上含 `1b5c1f4`+；证据 docs tip **`f3f804f`**（`63356c8` / `dd94137` 均为祖先） |
| 执行 | Mo-测试 |
| 入口 | **CLI**（`packages/solver-analytic/smoke/`）；**非** compose API / 前端报告组件 |
| 范围 | Q4-P06 退磁/导条温升 + Q4-P07 LPTN；**不**宣称解析 ≤5% / FEM ≤3%；**不开宣称 MVP** |

## 环境

- `git merge-base --is-ancestor 63356c8 HEAD` → exit 0。
- `git merge-base --is-ancestor dd94137 HEAD` → exit 0。
- `dd94137` 亦为 `63356c8` 祖先（`merge-base --is-ancestor dd94137 63356c8` → exit 0）。
- 工作目录：`/workspace/mo-platform/packages/solver-analytic`。
- 未改 `packages/` / `apps/` 业务代码；本记录与跟踪/清单更新仅 `docs/qa`。

## 必跑脚本结果（照实）

| 脚本 | exit code | stderr 摘要 | stdout 关键字段（照实） | 判定 |
| --- | --- | --- | --- | --- |
| `python3 smoke/run_demag_pm.py` | **0** | `# smoke OK demag_pm demagMargin=0.3421 B=0.8592 T  source=drive elapsed_ms=0.111` | `meta.solver=demag_pm`；`meta.source=drive`；`meta.mock=false`；**`pending_calibration: true`**（meta 与顶层均出现）；`demagMargin=0.342079`；`workingPoint.b_t=0.859248`；`workingPoint.temperature_c=100.0`；`demag.knee_b_t=0.48816`；`demag.load_line_pc=4.0`；`elapsed_ms≈0.111` | **PASS** |
| `python3 smoke/run_bar_temp_acim.py` | **0** | `# smoke OK bar_temp_acim barΔT=267.3 K endRingΔT=0 K  elapsed_ms=2.432` | `meta.solver=bar_temp_acim`；`meta.source=analytic`；`meta.mock=false`；**`pending_calibration: true`**；`barDeltaT_K=267.2734`；`endRingDeltaT_K=0.0`；`bar_temp.bar_temp_c=307.2734`；`bar_temp.end_ring_temp_c=40.0`；`bar_temp.ambient_c=40.0`；`lossesW.rotorBar=763.638158`；`lossesW.endRing=0.0`；`elapsed_ms≈2.43` | **PASS** |
| `python3 smoke/run_lptn_loop.py` | **0** | `# smoke OK lptn_loop iters=3 converged=True Tw=50.98C Tm=42.52C BrFactor=0.973 elapsed_ms=0.111` | `schemaVersion=thermal-loop-iter-v0`；`meta.solver=lptn_loop`；`meta.source=analytic`；`meta.mock=false`；**`pending_calibration: true`**；`meta.converged=true`；`iters` 长度 **3**（iter 0/1/2）；终态约 `nodes_c.copper=50.9894` / `magnet_or_bar=42.5227`；stderr `Tw=50.98C Tm=42.52C BrFactor=0.973`；`tol=0.05`；`max_iter=8`；末 residual≈`0.010467` | **PASS** |

### `pending_calibration`

三脚本 stdout JSON 均出现 **`pending_calibration: true`**（demag / bar：`meta` + 顶层；lptn：顶层 + `meta`）。**已注明；禁止据此宣称 ≤5% 达标。**

### demag 关键片段（stdout）

```json
{
  "meta": {
    "solver": "demag_pm",
    "source": "drive",
    "pending_calibration": true,
    "mock": false,
    "elapsed_ms": 0.111
  },
  "demagMargin": 0.342079,
  "workingPoint": {
    "b_t": 0.859248,
    "temperature_c": 100.0
  },
  "pending_calibration": true
}
```

### bar_temp 关键片段（stdout）

```json
{
  "meta": {
    "solver": "bar_temp_acim",
    "source": "analytic",
    "pending_calibration": true,
    "mock": false
  },
  "barDeltaT_K": 267.2734,
  "endRingDeltaT_K": 0.0,
  "bar_temp": {
    "bar_temp_c": 307.2734,
    "end_ring_temp_c": 40.0,
    "ambient_c": 40.0
  },
  "pending_calibration": true
}
```

### lptn 关键片段（stdout）

```json
{
  "schemaVersion": "thermal-loop-iter-v0",
  "pending_calibration": true,
  "meta": {
    "solver": "lptn_loop",
    "pending_calibration": true,
    "converged": true,
    "nodes_c": {
      "copper": 50.9894,
      "iron": 44.6542,
      "magnet_or_bar": 42.5227,
      "ambient": 25.0
    },
    "tol": 0.05,
    "max_iter": 8
  }
}
```

（`iters` 共 3 轮；完整数组见当次 stdout，此处不整表复述。）

## 未做 / 禁止宣称

- **未**勾选或宣称解析相对标杆 **≤5%** / FEM **≤3%**（`pending_calibration: true`；仍待校准书面关闭）。
- **未**测前端评估报告组件 / UI；本轮仅为 **CLI smoke**。
- **未**跑 compose API 热路径；**未**开宣称 MVP；**未**代签 Q4-P11。
- **未**改 `packages/` / `apps/` 业务代码。

## 跟踪 / 清单变更

| 项 | 变更 |
| --- | --- |
| Q4-P06 | **待测 → 通过（CLI smoke）**（证据 tip `63356c8` 叠 `dd94137`；备注 `pending_calibration`；禁勾 ≤5%） |
| Q4-P07 | **待测 → 通过（CLI smoke）**（证据 tip `63356c8`；备注 `pending_calibration`；禁勾 ≤5%） |
| P01–P05 / P08–P10 | 维持进行中（本轮不改） |
| P11 | 维持 **未开始** |
| 清单 Q4-C2 / Q4-C3 / Q4-D1 | **SKIP → PASS**（CLI smoke；非 UI 报告组件全量） |

## 结论

| 项 | 结论 |
| --- | --- |
| tip `63356c8`（叠 `dd94137`）解析 thermal CLI | **PASS**（三脚本 exit 0） |
| `pending_calibration` | **true**（三脚本均出现） |
| 对标 ≤5% / ≤3% | **未宣称**（禁止） |
| MVP | **未宣称** |
