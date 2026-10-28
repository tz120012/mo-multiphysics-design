# Q4 冒烟记录 — 驱动 tip `ab4bfda`（Q4-P01…P04）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:32 Asia/Shanghai |
| 指派 tip | **`ab4bfda`**（`feat(drive): Q4-1..4 BLDC/FOC/ACIM Vf+FOC + PWM/deadtime/efficiency Map`） |
| 仓库 HEAD（实测时） | **`ed831fd`**（`ab4bfda` 为祖先） |
| 执行 | Mo-测试 |
| 入口 | **pytest**（`packages/solver-drive` + `apps/api` Drive Jobs）；**非** DriveView UI 全量；Jobs 后端另线不挡本轮关项 |
| 范围 | Q4-P01 BLDC / Q4-P02 PMSM FOC / Q4-P03 ACIM V/f+感应 FOC / Q4-P04 PWM·死区·效率 Map；**不**宣称解析 ≤5% / FEM ≤3%；**不开宣称 MVP** |

## 环境

- `git merge-base --is-ancestor ab4bfda HEAD` → exit 0。
- 工作目录：`/workspace/mo-platform`。
- 未改 `packages/` / `apps/` 业务代码；本记录与跟踪/清单更新仅 `docs/qa`。
- 工作树另有他人 WIP（如 `apps/api` optimize / jobs 等未跟踪或已改文件）；**未** `git add` 那些路径。

## 必跑命令结果（照实）

### 1) `packages/solver-drive`

| 尝试 | 命令 | exit | 摘要 | 判定 |
| --- | --- | --- | --- | --- |
| A | `cd packages/solver-drive && python3 -m pytest tests/ -q` | **1** | `/usr/bin/python3: No module named pytest`（系统 Python 无 pytest） | 环境缺口；改用下方 B |
| B | `cd packages/solver-drive && /workspace/mo-platform/apps/api/.venv/bin/python -m pytest tests/ -q` | **0** | **`7 passed`** in 0.01–0.02s | **PASS** |

包内无独立 `.venv`；`pyproject.toml` 仅将 `pytest` 列为 optional `dev`。实测以 **API `.venv` 的 Python 3.13.5 + pytest 9.2.0** 跑通（`PYTHONPATH` 默认即包目录）。

#### 用例覆盖（`-v`）

| 测试 | 对应产品项 | 结果 |
| --- | --- | --- |
| `test_bldc_square_waveforms_and_losses` | P01 BLDC 方波 | PASSED |
| `test_pmsm_foc_id_iq` | P02 PMSM FOC | PASSED |
| `test_acim_vf_has_bar_endring` | P03 ACIM V/f | PASSED |
| `test_acim_foc_currents` | P03 ACIM 感应 FOC | PASSED |
| `test_pwm_deadtime_reduces_torque` | P04 PWM / 死区 | PASSED |
| `test_efficiency_map_3x3` | P04 效率 Map | PASSED |
| `test_run_drive_case_rejects_map_mode` | P04 入口边界 | PASSED |

### 2) `apps/api` Drive Jobs

| 命令 | exit | 摘要 | 判定 |
| --- | --- | --- | --- |
| `cd apps/api && .venv/bin/python -m pytest tests/test_drive_jobs.py -q` | **0** | **`5 passed`**, 2 warnings in ~1.0s | **PASS** |

#### 用例（`-v`）

| 测试 | 结果 |
| --- | --- |
| `test_drive_payload_validation_missing_mode` | PASSED |
| `test_drive_job_in_process_succeeds` | PASSED |
| `test_drive_sync_solve_rejects_map` | PASSED |
| `test_drive_sync_solve_ok` | PASSED |
| `test_efficiency_map_job` | PASSED |

警告（不否决）：Starlette/`httpx` TestClient 弃用提示；`HTTP_422_UNPROCESSABLE_ENTITY` 弃用提示。

## 可选：`/drive` 样例 JSON（只读形状）

路径：`apps/web/public/drive/`。

| 文件 | 解析 | 形状核对（不宣称精度） |
| --- | --- | --- |
| `bldc_square_sample.json` | OK | `mode=bldc_square`；含 `operatingPoint` / `lossesW` / `currentsA` / `waveforms` / `metrics` / `pwm` / `meta` |
| `pmsm_foc_sample.json` | OK | `mode=pmsm_foc`；字段同上（metrics 另含 `ldH`/`lqH`/`psiFWb`） |

本目录**未见** ACIM 样例 JSON；ACIM 覆盖以 pytest（`test_acim_*`）为准。**不**据此宣称数值精度。

## 未做 / 禁止宣称

- **未**勾选或宣称解析相对标杆 **≤5%** / FEM **≤3%**。
- **未**做 DriveView UI 全量 / 同屏对比（P05 另线进行中）。
- **未**开宣称 MVP；**未**代签 Q4-P11。
- **未**改 `packages/` / `apps/` 业务代码；**未**把他人 WIP 打进本 commit。

## 跟踪 / 清单变更

| 项 | 变更 |
| --- | --- |
| Q4-P01 | **待测 → 通过（pytest/CLI）**（BLDC：`test_bldc_square_*` + Jobs） |
| Q4-P02 | **待测 → 通过（pytest/CLI）**（PMSM FOC：`test_pmsm_foc_*` + Jobs） |
| Q4-P03 | **待测 → 通过（pytest/CLI）**（ACIM V/f + FOC：`test_acim_*`） |
| Q4-P04 | **待测 → 通过（pytest/CLI）**（PWM/死区/Map：`test_pwm_*` + `test_efficiency_map_*`） |
| P05 / P08 | 维持 **进行中** |
| P10 | 维持 **待测**（运维交测另线；本轮不改） |
| P06 / P07 / P09 | 维持 **通过**（本轮不改） |
| P11 | 维持 **未开始** |
| 清单 Q4-A1 / A2 / A3 | **SKIP → PASS**（pytest；非 UI） |
| 清单 Q4-B1 / B2 / B3 | **SKIP → PASS**（pytest；非 UI） |
| 清单 Q4-A4 | 维持 SKIP（本轮未做 Q2/Q3 基线抽查） |

## 结论

| 项 | 结论 |
| --- | --- |
| tip `ab4bfda` solver-drive pytest | **PASS**（7 passed；经 API `.venv`） |
| tip `ab4bfda` API `test_drive_jobs` | **PASS**（5 passed） |
| 对标 ≤5% / ≤3% | **未宣称**（禁止） |
| MVP | **未宣称** |
| 产品项 P01–P04 | **通过（pytest/CLI）**；备注非 UI / Jobs 后端另线 |

