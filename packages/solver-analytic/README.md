# packages/solver-analytic — 轻量解析（Wasm 目标）

Gate0 **已签字**（Motor G0-6）。Q1：径向 RF+PMSM **非线性 MEC** 已落地。Q2 进行中：MEC 加固（可复现 + 单测）、**ACIM 稳态等效电路**、材料消费适配器。Gate0 mock 保留回归。**本包不对标 ≤5%**。

维护：Mo-解析 · 仅 `/workspace/mo-platform`。

## 边界

| 能力 | 阶段 | 说明 |
| --- | --- | --- |
| 径向 MEC（PMSM） | **Q1 + Q2 加固** | 真实磁阻网络迭代；`meta.solver=mec`；固定 tol/iter，可复现 |
| 径向 MEC（BLDC） | Q2 近似 | 同 SPM 磁路 + 方波电流角/系数；`meta.bldc_approx`（完整梯形下一步） |
| Gate0 mock | 保留 | `solver=mock` / `smoke/run_radial_pmsm_mock.py` |
| ACIM 等效电路 | **Q2** | `meta.solver=acim_equiv`；Rs/Rr'/Xm/Xσ + 转差转矩 |
| 材料适配 | **Q2** | `materials_adapter.py`：内联 / catalog id / 工程默认 |
| 轴向多平面展开 | Q3 | 盘式径向解耦圆环积分 |
| Wasm | **Q2** | `packages/solver-analytic-wasm/`（`solve_json`）；见该包 README |
| Sync HTTP | **Q2 可选** | `POST /api/v1/solver/analytic/solve`（Bearer）薄包装本包 `solve()` |

**不做**：FEM 网格/求解、几何参数化本体、电调后处理 UI。

## 目录

```
packages/solver-analytic/
  README.md
  solve.py                 # 统一入口 solver=mec|mock（默认 mec）
  materials_adapter.py     # 材料 id / 内联 / 默认
  api/                     # JSON schema + 样例
  radial_mec/              # 径向非线性 MEC（PMSM/BLDC）
  machines/acim_equiv.py   # ACIM 稳态等效电路
  axial_planes/            # Q3 占位
  smoke/
    run_radial_pmsm_mock.py
    run_radial_pmsm_mec.py
    run_radial_acim_equiv.py
    fixtures/radial_pmsm_request.json
    fixtures/radial_acim_request.json
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
python3 packages/solver-analytic/radial_mec/tests/test_reluctance_convergence.py
python3 packages/solver-analytic/radial_mec/tests/test_materials_adapter.py
```

范围草案：`docs/drafts/解析范围.md`。
