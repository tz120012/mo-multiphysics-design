# packages/solver-analytic — 轻量解析（Wasm 目标）

Gate0 / Q1 / Q2 / Q3 **已签字**。Q4 进行中：退磁 / 导条温升 / LPTN（`thermal/`）。Gate0 mock 保留回归。**本包不对标 ≤5%**。

维护：Mo-解析 · 仅 `/workspace/mo-platform`。

## 边界

| 能力 | 阶段 | 说明 |
| --- | --- | --- |
| 径向 MEC（PMSM） | **Q1 + Q2 加固** | 真实磁阻网络迭代；`meta.solver=mec`；固定 tol/iter，可复现 |
| 径向 MEC（BLDC） | Q2 近似 | 同 SPM 磁路 + 方波电流角/系数；`meta.bldc_approx`（完整梯形下一步） |
| Gate0 mock | 保留 | `solver=mock` / `smoke/run_radial_pmsm_mock.py` |
| ACIM 等效电路 | **Q2** | `meta.solver=acim_equiv`；Rs/Rr'/Xm/Xσ + 转差转矩 |
| 材料适配 | **Q2** | `materials_adapter.py`：内联 / catalog id / 工程默认 |
| 轴向多平面展开 | **Q3-1 MVP** | AF+PMSM；`meta.solver=axial_planes`；见 `axial_planes/README.md` |
| 退磁工作点（PM） | **Q4-6 MVP** | `thermal/demag.py` → `demagMargin`；`pending_calibration` |
| ACIM 导条温升 | **Q4-6 MVP** | `thermal/bar_temp.py` → `barDeltaT_K` / `endRingDeltaT_K` |
| LPTN 温漂闭环 | **Q4-7 MVP** | `thermal/lptn.py`；`schemaVersion=thermal-loop-iter-v0`；对齐 FEM tip `864ec20` |
| Wasm | **Q2** | `packages/solver-analytic-wasm/`（`solve_json`）；见该包 README |
| Sync HTTP | **Q2 可选** | `POST /api/v1/solver/analytic/solve`（Bearer）薄包装本包 `solve()` |
| Q6 再求解组装 | **Q6-3** | `api/compose_request.py`：`GeometrySummary`+材料+OP → `SolveRequest`；冒烟 `smoke/run_q6_rerun_closed_loop.py`；契约 `docs/drafts/Q6-解析-改参再求解闭环.md` |

**不做**：FEM 网格/求解、几何参数化本体、电调后处理 UI。

## 目录

```
packages/solver-analytic/
  README.md
  solve.py                 # 统一入口 solver=mec|mock（默认 mec）
  materials_adapter.py     # 材料 id / 内联 / 默认
  api/                     # JSON schema + compose_request + 样例
  radial_mec/              # 径向非线性 MEC（PMSM/BLDC）
  machines/acim_equiv.py   # ACIM 稳态等效电路
  axial_planes/            # Q3 AF+PMSM 多平面展开
  thermal/                 # Q4 退磁 / 导条温升 / LPTN
  smoke/
    run_radial_pmsm_mock.py
    run_radial_pmsm_mec.py
    run_radial_acim_equiv.py
    run_axial_pmsm_planes.py
    run_demag_pm.py
    run_bar_temp_acim.py
    run_lptn_loop.py
    fixtures/…
```

## 接口

`api/solve.schema.json`：`SolveRequest` → `SolveResult`（`meta.solver` 枚举扩展 `acim_equiv`，向后兼容）。

### 前端最小调用

```bash
# PMSM MEC（默认）
python3 packages/solver-analytic/solve.py --solver=mec \
  packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json

# Gate0 mock
python3 packages/solver-analytic/solve.py --solver=mock \
  packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json

# ACIM 等效电路（machine_type=ACIM → meta.solver=acim_equiv）
python3 packages/solver-analytic/solve.py --solver=mec \
  packages/solver-analytic/smoke/fixtures/radial_acim_request.json
```

Python：

```python
from solve import solve
import json
req = json.load(open("packages/solver-analytic/smoke/fixtures/radial_acim_request.json"))
result = solve(req, solver="mec")  # result["meta"]["solver"] == "acim_equiv"
```

ACIM 工况优先给 `operating_point.voltage_v_peak`（相电压峰值）+ `speed_rpm`；`slip` / `freq_hz` 可省略（默认 50 Hz，滑差由同步速推算）。`losses_w.rotor_bar` 必有。`back_emf_v_peak` 槽位映射为气隙/感应电压峰值。

材料：内联 `br_t` / `sigma_copper` / `sigma_bar`，或 `steel_id`/`magnet_id`/`conductor_id`/`bar_id` + 可选顶层 `materials_catalog`。期望 meta 键见 `docs/drafts/材料消费字段.md`。

## 冒烟 / 测试

```bash
python3 packages/solver-analytic/smoke/run_radial_pmsm_mock.py
python3 packages/solver-analytic/smoke/run_radial_pmsm_mec.py
python3 packages/solver-analytic/smoke/run_radial_acim_equiv.py
python3 packages/solver-analytic/smoke/run_axial_pmsm_planes.py
python3 packages/solver-analytic/smoke/run_demag_pm.py
python3 packages/solver-analytic/smoke/run_bar_temp_acim.py
python3 packages/solver-analytic/smoke/run_lptn_loop.py
python3 packages/solver-analytic/radial_mec/tests/test_reluctance_convergence.py
python3 packages/solver-analytic/radial_mec/tests/test_materials_adapter.py
python3 packages/solver-analytic/axial_planes/tests/test_axial_planes.py
```

范围草案：`docs/drafts/解析范围.md`；Q4：`docs/drafts/Q4-热与退磁.md`（损耗契约对齐 `Q4-7-热闭环-FEM损耗输入.md`）。
