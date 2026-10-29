# Q7-2 激励 / drive → UEM（短契约 · Mo-驱动）

> 开闸 tip `30a37a7` · **零新 API** · 复用既有 `POST /api/v1/jobs` `jobType=drive`（可选仍保留 `POST /api/v1/drive/solve`）  
> 主验收面：工作台 `?step=excitation`（`/drive` 已 redirect）。**禁止**新 `/excitation/*`；**禁止**改 `packages/solver-drive` 求解核心。

## UEM 切片

`UemExcitationState`（`apps/web/src/lib/geometryDefaults.ts`）：

| 字段 | 键风格 | 说明 |
| --- | --- | --- |
| `operatingPoint` | **蛇形**（解析/UEM） | `speed_rpm` / `current_a_peak` / `gamma_deg` / `voltage_v_peak` / `freq_hz` / `slip` |
| `driveDraft?` | 草稿 | `mode` / `pwm` / `deadTime` / 可选 `iqA` `idA` `torqueNm` `tempC` `slip` |

`defaultExcitation` 按机型给默认 `driveDraft.mode`（BLDC→`bldc_square`，PMSM→`pmsm_foc`，ACIM→`acim_vf`）。

会话：`setDriveDraft(partial | undefined)` 合并写；保留 `setDriveMode`。

## 组装 → DriveJobPayload

`composeDrivePayloadFromUem({ machineType, excitation, map? })` → `@/api/types` `DriveJobPayload`：

| UEM | Drive payload |
| --- | --- |
| `operatingPoint.speed_rpm` | `operatingPoint.speedRpm` |
| `operatingPoint.current_a_peak` | 启发为 `iqA`（BLDC/PMSM/FOC；`driveDraft.iqA` 优先） |
| `operatingPoint.slip` / `voltage_v_peak` / `freq_hz` | `slip` / `voltageVPeak` / `freqHz`（ACIM） |
| `driveDraft.mode` | `mode` |
| `driveDraft.pwm` / `deadTime` | 同名驼峰对象 |
| `driveDraft.torqueNm` `tempC` `idA`… | 写入 `operatingPoint` 覆盖 |

- **`source` 不进 payload**（Jobs 已有）。
- 结果仍是既有 drive 契约：`payload.result` 含 `metrics` / `lossesW` / `currentsA` / `waveforms`；`resultRef`=`drive://jobs/{id}`。
- 详见 [驱动Jobs契约.md](./驱动Jobs契约.md)。

## 工作台激励步（Q7-C2）

- OP/工况写 UEM（蛇形键保持）；可选编辑 `driveDraft.mode` + PWM/死区。
- **本步可不强制跑 Jobs**；「用现有 drive Job 预览」= `createJob`+`pollJob`，`jobType=drive`，payload 来自 compose。
- 预览摘要可折叠（Tavg / η / lossesW）；失败明示；**不宣称精度**。

## 非目标

- 新激励 REST；扩拓扑矩阵；改 solver-drive 算法；宣称 ≤5%/≤3% / 全功能 Maxwell；代关 Q7 跟踪表。
