# Q5-2 FE — `/field` 磁静力学后处理

| 字段 | 内容 |
| --- | --- |
| 角色 | Mo-前端 |
| 代码 | `apps/web/src/views/FieldVizView.vue`、`apps/web/src/types/fieldViz.ts`、`apps/web/src/lib/fieldPostprocess.ts` |
| 对照 | FEM tip **`797ce67`**；[Q5-2-真磁静力学后处理](../drafts/Q5-2-真磁静力学后处理.md) |
| 数据 | 仍只读 Jobs artifacts（F1 triad + manifest）。无新 API。 |
| 性质 | 路径说明，**不是**冒烟 PASS，**不**关 Q5-B1 / Q3-L4。 |

## 判定

| 条件 | 面板 |
| --- | --- |
| `equationMode=magnetostatic`，或 `magnetostaticPathReady=true` | **磁静力学后处理**：`postprocess`（如 maxwell）、`axialForceN`、`magneticEnergyJ`、`bearingLoadN`、`deflectionHintMm`、`torqueNm`、`lossesW`、`dryRun`、`elmerExit` |
| `equationMode=heat_proxy`，或未标注 equationMode（旧 fixture / 兼容路径） | **heat-proxy / 非磁静力学真值**。不把轴向力或磁能标成磁静力学真值 |
| `pending_calibration` 为 true，或两侧都缺该键 | 徽章 `pending_calibration`。`axialForceN` / `magneticEnergyJ` 旁同样标注未校准 |

缺键显示为 —；JSON `null` 显示为 null（与 0 区分）。旧 fixture 无这些键时仍可打开 `/field`。

真路径标量形状（tip `797ce67`）：`equationMode=magnetostatic`、`magnetostaticPathReady=true`、`pending_calibration=true`、`postprocess=maxwell`、`axialForceN`、`magneticEnergyJ`、`dryRun=false`、`elmerExit=0`。数值未校准，不宣称误差达标，不宣称 MVP。

## 抽查

| URL | 期望 |
| --- | --- |
| `/field` 或 `/field?source=fixture` | `source=fixture`；面板为 heat-proxy / 非磁静力学真值；有 pending_calibration 徽章 |
| `/field?jobId=<磁静力学 scalars 的任务>` | `source=job-artifacts`；标题为磁静力学后处理；能看到 maxwell、`axialForceN`、`magneticEnergyJ`；pending_calibration 为 true 时力/能量标为未校准 |
| `/field?jobId=<heat-proxy 或旧产物>` | 不出现「磁静力学后处理」标题 |
| `/field?jobId=<同上>&source=fixture` | 仍为 public fixture（与 Q4+-3 相同） |
