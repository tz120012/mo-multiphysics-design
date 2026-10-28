# packages/solver-analytic — 轻量解析（Wasm 目标）

Gate0 **已签字**（Motor G0-6）。Q1：径向 RF+PMSM **非线性 MEC 初版**已落地；Gate0 mock 保留回归。完整 ACIM / 径向全机型对标 ≤5% 仍属 Q2，**本包不对标 ≤5%**。

维护：Mo-解析 · 仅 `/workspace/mo-platform`。

## 边界

| 能力 | 阶段 | 说明 |
| --- | --- | --- |
| 径向 MEC（PMSM） | **Q1 初版** | 真实磁阻网络迭代；`meta.solver=mec` |
| Gate0 mock | 保留 | `solver=mock` / `smoke/run_radial_pmsm_mock.py` |
| ACIM 等效电路 | Q2 | 与 MEC 叠加；转差 / 导条电阻 |
| 轴向多平面展开 | Q3 | 盘式径向解耦圆环积分 |
| Wasm | Q2+ | C++ 或 Rust → WebAssembly（任务书冻结） |

**不做**：FEM 网格/求解、几何参数化本体、电调后处理 UI。

## 目录

```
packages/solver-analytic/
  README.md
  solve.py             # 统一入口 solver=mec|mock（默认 mec）
  api/                 # JSON schema + 样例
  radial_mec/          # 径向非线性 MEC（PMSM）
  axial_planes/        # Q3 占位
  machines/            # bldc | pmsm | acim 占位
  smoke/
    run_radial_pmsm_mock.py
    run_radial_pmsm_mec.py
    fixtures/radial_pmsm_request.json
```

## 接口

`api/solve.schema.json`：`SolveRequest` → `SolveResult`。

```bash
python3 packages/solver-analytic/solve.py --solver=mec
python3 packages/solver-analytic/solve.py --solver=mock
```

## 冒烟

```bash
python3 packages/solver-analytic/smoke/run_radial_pmsm_mock.py
python3 packages/solver-analytic/smoke/run_radial_pmsm_mec.py
python3 packages/solver-analytic/radial_mec/tests/test_reluctance_convergence.py
```

范围草案：`docs/drafts/解析范围.md`。
