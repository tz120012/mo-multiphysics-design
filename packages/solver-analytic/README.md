# packages/solver-analytic — 轻量解析（Wasm 目标）

Gate0 **骨架**。完整业务算法自 Q2（径向 MEC + ACIM 等效电路）起实现；轴向多平面见 Q3。

维护：Mo-解析 · 仅 `/workspace/mo-platform`。

## 边界

| 能力 | 阶段 | 说明 |
| --- | --- | --- |
| 径向 MEC | Q2 | 非线性磁路，秒级初选 |
| ACIM 等效电路 | Q2 | 与 MEC 叠加；转差 / 导条电阻 |
| 轴向多平面展开 | Q3 | 盘式径向解耦圆环积分 |
| Wasm | Q2+ | C++ 或 Rust → WebAssembly（任务书冻结） |

**不做**：FEM 网格/求解、几何参数化本体、电调后处理 UI。

## 目录

```
packages/solver-analytic/
  README.md
  api/                 # JSON schema + 样例
    solve.schema.json
    examples/
  radial_mec/          # Q2 占位
  axial_planes/        # Q3 占位
  machines/            # bldc | pmsm | acim 占位
  smoke/               # Gate0 冒烟（mock）
    run_radial_pmsm_mock.py
    fixtures/radial_pmsm_request.json
```

## 接口（草案）

`api/solve.schema.json`：`SolveRequest` → `SolveResult`。

- 输入：拓扑、机型、几何摘要、材料、工况
- 输出：转矩、反电势峰值、损耗粗算、`meta.elapsed_ms`

与 Mo-架构评审后冻结；Wasm 与可选轻量后台共用同一 schema。

## Gate0 冒烟

```bash
python3 packages/solver-analytic/smoke/run_radial_pmsm_mock.py
```

径向 PMSM 假数据 → 数值输出（mock，不对标）。范围草案：`docs/drafts/解析范围.md`。
