# packages/solver-drive — 工程级驱动模型（Q4-1…4）

纯 Python 工程模型（**非**全开关 SPICE）。覆盖 BLDC 方波、PMSM FOC、ACIM V/f + 感应 FOC、PWM/死区修正、效率 Map。

维护：Mo-驱动 · 仅 `/workspace/mo-platform`。

## 边界 / 声明

- **不宣称**解析 ≤5% 或 FEM ≤3% 等误差指标；本包为可复现工程近似，供 UI / Jobs / 热接口消费。
- **不**硬依赖 FEM；可选消费 analytic 结果字段（若 payload 带入）。
- 效率 Map 默认 **20×20**（转速×转矩），可配置；扫描须走 API Jobs（Celery 或 in-process 假异步），禁止浏览器长阻塞。

## 入口

```python
from solve import run_drive_case, run_efficiency_map

result = run_drive_case({
    "mode": "pmsm_foc",          # bldc_square|pmsm_foc|acim_vf|acim_foc
    "machineType": "PMSM",
    "operatingPoint": {"speedRpm": 3000, "torqueNm": 5.0, "tempC": 80},
    "plant": {"Rs": 0.05, "Ld": 1e-3, "Lq": 1.2e-3, "psi_f": 0.08, "p": 4, "Vdc": 48},
    "pwm": {"carrierHz": 10000, "modIndex": 0.9, "scheme": "svpwm"},
    "deadTime": {"tdeadUs": 1.0},
})

emap = run_efficiency_map({
    "mode": "pmsm_foc",
    "machineType": "PMSM",
    "mapGrid": {"nx": 20, "ny": 20, "speedRpmMin": 500, "speedRpmMax": 6000,
                "torqueNmMin": 0.5, "torqueNmMax": 10},
    "plant": {...},
})
```

## 对外结果字段（与 Mo-解析 Q4-6 对齐）

单工况 `result` 至少含：

| 字段 | 说明 |
| --- | --- |
| `lossesW` | `{ copper, iron, magnetEddy, bar, endRing }`（W；不适用可为 `null`） |
| `currentsA` | `{ rmsPhase, id, iq }` |
| `operatingPoint` | 含 `speedRpm` / `torqueNm` / `tempC` 等 |
| `waveforms` | `t_s`, `ia`, `ib`, `ic`, `torque_nm` 时间序列 |
| `metrics` | `torqueAvgNm`, `torqueRipplePpNm`, `efficiency`, … |

效率 Map：`axes` + `efficiency`（二维，越界/不可行为 `null`）+ `meta`。

## 测试

```bash
cd packages/solver-drive && python3 -m pytest -q
```
