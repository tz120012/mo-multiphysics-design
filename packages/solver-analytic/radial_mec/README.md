# radial_mec — 径向非线性磁路（MEC）

Gate0 已签字；Q1 落地 **RF + PMSM**；Q2 加固可复现 / 单测，并允许 **BLDC 同磁路近似**。

维护：Mo-解析 · 仅 `/workspace/mo-platform`。

## 能力

| 项 | 说明 |
| --- | --- |
| 拓扑 | 表面贴装（SPM）近似：永磁 → 气隙 → 定子齿 → 定子轭 → 转子轭（串联单极路径） |
| 非线性 | 解析 μ(B) 钢；定点迭代 Φ = F / ΣR(B)；**固定 `MEC_TOL` / `MEC_MAX_ITER`** |
| 出口 | 气隙磁密、磁链/反电势峰值、电磁转矩、铜/铁损粗算、Ld/Lq 增量粗估 |
| API | `solve_radial_pmsm_mec(request) -> dict`（`meta.solver="mec"`，`mock=false`；BLDC 时 `meta.bldc_approx=true`） |

ACIM 不在本目录：见 `machines/acim_equiv.py`。Gate0 mock：`smoke/run_radial_pmsm_mock.py`。

## 模块

```
radial_mec/
  materials.py   # μ0、钢 μ(B)、永磁 Hc
  geometry.py    # GeometrySummary → 支路长/面积
  network.py     # 磁阻元 + 非线性迭代（纯 I/O）
  pmsm.py        # 工况 → SolveResult（经 materials_adapter）
  tests/         # 磁阻 / 收敛 / 可复现 / T(I) / mock×mec
```

## 已知简化

- 轭/齿高由摘要字段估算；缺省写入 `meta.note`
- BLDC 为方波系数近似，非完整梯形换相模型
- 损耗为 Steinmetz / I²R 量级粗算，**不对标 ≤5%**
