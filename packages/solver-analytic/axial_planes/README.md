# axial_planes — 轴向多平面展开（Q3-1）

| 字段 | 内容 |
| --- | --- |
| 维护 | Mo-解析 |
| 阶段 | **Q3-1 MVP**：AF + PMSM（Python 金标） |
| 状态 | 可运行工程初版；**不对标 ≤5%**；golden `pending_calibration` |
| 契约 | 同形 `../api/solve.schema.json`（`topology=AF`）；`meta.solver=axial_planes` |
| 快照 | 仍写入 `.mems` **`solver/analytic/`**（不新建 `solver/axial/`） |
| 部署 | sync `POST /solver/analytic/solve` **或** Jobs `analytic` 均可；**Wasm AF = stretch**，非 Q3 关门 |
| 锁定 | [`docs/drafts/Q3-轴向与FEM边界.md`](../../../docs/drafts/Q3-轴向与FEM边界.md)（架构 tip `8d966d9`） |

## 1. 原理

盘式轴向电机气隙磁通沿 **轴向（z）** 穿过气隙；转矩力臂沿 **半径 r**。多平面展开把环形气隙在径向上解耦为 **N 个同心圆环（平面）**：

1. 给定内/外半径 \(R_i, R_o\)，等宽分环 \(\Delta r = (R_o - R_i)/N\)。
2. 第 \(k\) 环取均值半径 \(r_k\)、径向宽度 \(\Delta r_k\)。
3. 局部周向极距 \(\tau_{p,k} = 2\pi r_k / N_\mathrm{poles}\)。
4. 一极气隙/磁钢等效面积 \(A_k = \alpha_m\,\tau_{p,k}\,\Delta r_k\)（**周长弧 × 径向宽度**，不用径向机的 `stack_length` 硬套为叠长）。
5. 轴向路径长度：磁钢厚 \(h_m\)、等效气隙 \(g_\mathrm{eff}=k_c g\)、齿/轭轴向厚度由盘厚与估算得出。
6. 每环建 **串联单极磁路**（PM → 气隙 → 定子齿 → 定子轭 → 转子轭），复用 `radial_mec.network` 的 μ(B) 定点迭代。
7. 各环磁通 \(\Phi_k\) 叠加得相磁链 \(\psi_\mathrm{pm} = k_w N_\mathrm{ph}\sum_k\Phi_k\)，再算转矩 / 反电势 / 损耗。

### 与径向 MEC 的关系

| | 径向 `radial_mec` | 轴向 `axial_planes` |
| --- | --- | --- |
| 拓扑 | `RF` | `AF` |
| 气隙法向 | 径向 | 轴向 |
| 积分方向 | 轴向叠长 \(L\) | 径向分环 \(\Delta r\) |
| 磁阻核 | `network.solve_series_mec` | **同一套** |
| `meta.solver` | `mec` | `axial_planes` |

材料与工况接口共用：`materials_adapter` + `operating_point`。

## 2. 假设与局限

- **MVP 仅 AF + PMSM**；AF+BLDC / AF+ACIM **未实现**（`solve.py` 明确 `ValueError`）。
- 环间无径向漏磁耦合；多盘 `disk_count` 仅 meta 记录，默认单气隙等效。
- 齿/轭厚度缺省时按内外径与盘厚估算，写入 `meta.note`。
- 铜/铁/磁钢涡流为量级粗算；**禁止宣称相对标杆 ≤5%**。
- 无标定 golden → `pending_calibration`。

## 3. 输入 / 输出

### 几何摘要（AF，与 FE stub 对齐）

| 字段 | 说明 |
| --- | --- |
| `rotor_od_m` | 外 **直径**（stub 映射） |
| `stator_id_m` | 内 **直径**（stub 映射） |
| 或 `outer_radius_m` / `inner_radius_m` | 半径优先写法 |
| `stack_length_m` | AF：盘/轴向铁厚（非 RF 叠长）；亦可 `disk_thickness_m` |
| `airgap_m`, `magnet_thickness_m` | 轴向气隙 / 磁钢厚 |
| `poles`, `slots`, `turns_per_phase` | 极槽与匝数 |
| `n_planes` | 分环数（默认 4，≥1） |

### 输出（SolveResult）

- `torque_nm`, `back_emf_v_peak`, `losses_w`, `inductance_h`
- `meta.solver="axial_planes"`, `meta.mock=false`, `meta.n_planes`, `meta.elapsed_ms`
- `meta.axial.planes[]`（每环 \(r, \Phi, B_g\)）, `meta.note`

## 4. 用法

```bash
python3 packages/solver-analytic/smoke/run_axial_pmsm_planes.py
# fixture: smoke/fixtures/axial_pmsm_request.json
# FE UI 临时 stub（非 golden）: axial_pmsm_stub_*.json

python3 packages/solver-analytic/solve.py \
  packages/solver-analytic/smoke/fixtures/axial_pmsm_request.json
```

```python
from solve import solve
out = solve(req)  # topology=AF, machine_type=PMSM
assert out["meta"]["solver"] == "axial_planes"
assert out["meta"]["mock"] is False
```

HTTP（BE 已挂同一 `solve()` 时）：

```bash
curl -s -X POST "$BASE/api/v1/solver/analytic/solve" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d @packages/solver-analytic/smoke/fixtures/axial_pmsm_request.json
```

## 5. 目录

```
axial_planes/
  README.md      # 本说明
  __init__.py
  geometry.py    # 分环 + 每环支路长/面积
  pmsm.py        # AF+PMSM → SolveResult
  tests/         # 可复现 / n_planes / 非法组合
```

## 6. 下一步（非本轮硬门禁）

- AF+BLDC / AF+ACIM
- 多盘气隙串联/并联显式模型
- Wasm AF（stretch / fast-follow）
- 标杆校准后填 golden
