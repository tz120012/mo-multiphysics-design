# radial_mec — 径向非线性磁路（MEC）

Gate0 已签字；Q1 起落地**径向 RF + PMSM** 工程初版（真实磁阻网络迭代，非 mock 缩放）。

维护：Mo-解析 · 仅 `/workspace/mo-platform`。

## 能力

| 项 | 说明 |
| --- | --- |
| 拓扑 | 表面贴装（SPM）近似：永磁 → 气隙 → 定子齿 → 定子轭 → 转子轭（串联单极路径） |
| 非线性 | 解析 μ(B) 钢；定点迭代 Φ = F / ΣR(B) 至相对收敛 |
| 出口 | 气隙磁密、磁链/反电势峰值、电磁转矩、铜/铁损粗算、Ld/Lq 增量粗估 |
| API | `solve_radial_pmsm_mec(request: dict) -> dict`（对齐 `SolveResult`，`meta.solver="mec"`，`mock=false`） |

**不做（本包）**：完整 ACIM、轴向多平面、FEM、对标 ≤5% 校准。Gate0 mock 仍在 `smoke/run_radial_pmsm_mock.py`。

## 模块边界（便于日后 Wasm）

```
radial_mec/
  materials.py   # μ0、钢 μ(B)、永磁 Hc
  geometry.py    # GeometrySummary → 支路长/面积
  network.py     # 磁阻元 + 非线性迭代（无 I/O）
  pmsm.py        # 工况 → SolveResult
  tests/         # 磁阻 / 收敛轻量测试
```

数值核与 JSON 编解码分离：Wasm 时可只移植 `materials` / `network` / 几何公式。

## 调用

```bash
PYTHONPATH=packages/solver-analytic python3 -c "
from radial_mec import solve_radial_pmsm_mec
import json
print(solve_radial_pmsm_mec(json.load(open('packages/solver-analytic/smoke/fixtures/radial_pmsm_request.json'))))
"
```

或统一入口：`python3 -m` 见上层 `solve.py` / 冒烟脚本。

## 已知简化

- 轭/齿高由摘要字段估算（schema 无定子外径）；缺省写入 `meta.note`
- 电枢反应仅粗分 d/q；忽略交叉饱和与局部漏磁细模
- 损耗为 Steinmetz / I²R 量级粗算，**不对标 ≤5%**
