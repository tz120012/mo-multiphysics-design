# rf-pmsm-creator-001

| 字段 | 内容 |
| --- | --- |
| 机型 | PMSM（径向 RF，内转子） |
| 极 / 槽 | **4 / 6**（非 smoke 的 10p/12s 或 demo 6p/18s） |
| 标杆来源 | 公开文献 CREATOR：**arXiv [2501.15921](https://arxiv.org/abs/2501.15921)**；COMPEL `10.1108/compel-11-2024-0462`；数据集 DOI `10.3217/sns1d-77m43` |
| 几何工厂 | `mo_geometry.creator_radial_pmsm_4p6s()` |
| 校准 / golden | **已标定 ≤5%**（Mo-解析）；golden `tests/benchmark/golden/rf-pmsm-creator-001.json`；`pending_calibration=false`；报告 `docs/qa/reports/标定报告-解析-20261028-Q5-3.md`；**待交测复现，勿勾 F1** |
| NC 数据 | **未**整包入库 CREATOR NC 二进制；仅公开表标量 |

## 论文表指针

| 表 | 用途 |
| --- | --- |
| **Table 12** | 几何主表（定转子直径、气隙、叠长、磁钢径向厚/高/跨距、槽口等）→ `input/geometry_params.json` |
| **Table 9** | 绕组：turns per slot = **328**，1 layer，concentrated tooth-wound |
| **Table 6** | 额定附近：**~0.10 Nm @ 2000 rpm** |
| **Table 7** | 材料标签：M250-35A / sintered ferrite（径向磁化）— 仅 meta，非 materials-service 绑定 |
| **Table 8** | Inom = **0.21 Arms** → analytic 骨架 `current_a_peak ≈ √2×0.21` |
| **Table 10** | Rs / λpm / E0 参考写入 analytic `meta`（非 golden） |

磁钢：论文 **inset** → 几何 `magnetTopology="IPM"`（勿用 SPM）。

气隙校核：`rotor OD 47 + 2×0.4 = stator ID 47.8`。

## turns_per_phase 假设

单层集中绕组（tooth-wound）常用派生：

```text
turns_per_phase = (slots / phases) * turns_per_slot
                = (6 / 3) * 328
                = 656
```

写清于 `input/analytic_request.json` → `meta.turns_assumption`；解析可改。

## 本目录文件

| 文件 | 说明 |
| --- | --- |
| `case.json` | id / topology / machine / source / metrics |
| `input/geometry_params.json` | 与 `packages/geometry/examples/radial_pmsm_creator_4p6s_params.json` 一致（mm） |
| `input/geometry_summary.json` | SI GeometrySummary（4 poles / 6 slots） |
| `input/analytic_request.json` | SolveRequest 骨架（可拷 smoke fixtures 试用；**非 golden**） |

权威短文：`docs/drafts/几何-Q5-3-CREATOR-PMSM-4p6s.md`。

## 禁项

- 勿拷贝 `rf-pmsm-smoke-001` 的 10p/12s（或其它）几何当本 case 输入
- 勿入库 NC 二进制包
- 勿勾 F1 / 勿宣称 MVP（golden 已由 Mo-解析按报告写入；交测前勿再改）
