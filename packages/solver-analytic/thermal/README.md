# thermal/ — Q4 退磁 / 导条温升 / LPTN

Mo-解析内核。**不对标 ≤5%**；出口恒 `pending_calibration=true`。

| 模块 | 用途 | 冒烟 |
| --- | --- | --- |
| `demag.py` | 永磁退磁裕度 `demagMargin` | `smoke/run_demag_pm.py` |
| `bar_temp.py` | ACIM `barDeltaT_K` / `endRingDeltaT_K` | `smoke/run_bar_temp_acim.py` |
| `lptn.py` | 简化 LPTN + 温漂闭环；`schemaVersion=thermal-loop-iter-v0` | `smoke/run_lptn_loop.py` |
| `io_adapt.py` | 驱动别名 → FEM 权威 `lossesW` 键 | — |

损耗/迭代字段名强制对齐：`docs/drafts/Q4-7-热闭环-FEM损耗输入.md`（FEM tip `864ec20`）。  
域草案：`docs/drafts/Q4-热与退磁.md`。

驱动别名：`bar`→`rotorBar`，`magnetEddy`→`pmEddy`。自产损耗 `source=analytic`。
