# 驱动 Jobs 契约（短笺 · Q4-1…4）

> 真理源：`DriveJobPayload` in `apps/api/app/schemas/common.py` + `docs/drafts/openapi-v1.yaml`。

## Enqueue

`POST /api/v1/jobs` · `jobType=drive` · Bearer

```json
{
  "projectId": "<uuid>",
  "jobType": "drive",
  "payload": {
    "mode": "pmsm_foc",
    "machineType": "PMSM",
    "operatingPoint": { "speedRpm": 3000, "iqA": 10, "tempC": 80 },
    "pwm": { "carrierHz": 10000, "modIndex": 0.9, "scheme": "svpwm" },
    "deadTime": { "tdeadUs": 1.0 },
    "plant": { "Rs": 0.05, "Ld": 0.001, "Lq": 0.0012, "psi_f": 0.08, "p": 4, "Vdc": 48 }
  }
}
```

`mode=efficiency_map` 时附 `mapGrid`（默认 nx=ny=20）与可选 `mapMode`；**禁止**在 FastAPI 请求线程同步扫 Map。

## 结果

- `resultRef`: `drive://jobs/{jobId}`
- `payload.result`：单工况含 `lossesW` / `currentsA` / `operatingPoint` / `waveforms` / `metrics`；Map 含 `axes` + `efficiency[][]`。

可选预览：`POST /api/v1/drive/solve`（仅单工况）。

## 消费字段

- `source`: `drive`
- `lossesW` / `currentsA` / `operatingPoint`（驱动权威名）
- Mo-解析适配：`magnetEddy→pmEddy`，`bar→rotorBar`，`speedRpm→rpm`，`tempC`=磁体温度
- FE 静态样例：`/drive/bldc_square_sample.json`、`/drive/pmsm_foc_sample.json`（public）
- `metrics` 可导出客观量（torqueAvgNm / ripplePpNm / efficiency / pMechW / pElecW）；驱动不写 NSGA 核心

