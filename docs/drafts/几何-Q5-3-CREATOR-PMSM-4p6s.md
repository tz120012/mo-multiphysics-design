# 几何 Q5-3：CREATOR 径向 PMSM 4 极 / 6 槽

| 项 | 值 |
| --- | --- |
| 角色 | Mo-几何 |
| 状态 | 几何侧落地（参数工厂 + examples + analytic 骨架）；**非** golden / 非 MVP 宣称 |
| 标杆 case | `tests/benchmark/cases/rf-pmsm-creator-001/` |
| 工厂 | `mo_geometry.creator_radial_pmsm_4p6s()` |
| 文献 | arXiv [2501.15921](https://arxiv.org/abs/2501.15921)；COMPEL `10.1108/compel-11-2024-0462`；数据集 DOI `10.3217/sns1d-77m43` |

## 声明

- **未**整包入库 CREATOR NC 数据包二进制；本仓库仅写入公开论文表中的几何/绕组标量。
- 许可：**CC BY-NC** 待用户确认；消费方勿把 NC 数据当可再分发资产。
- 几何 tip 用途：供 Mo-解析拷贝 analytic 骨架 / case 输入做接线与标定；**不**翻转 `pending_calibration`，**不**写真实 golden，**不**宣称 ≤5%。

## 论文表对照（写入 mo_geometry）

单位：`units.length=mm`。来源：**Table 12**（几何），绕组/额定见 Table 6/9 等。

| 论文 (Table 12) | 值 | mo_geometry |
| --- | --- | --- |
| Stator outer diameter | 113 mm | `stator.outerDiameter=113` |
| Stator inner diameter | 47.8 mm | `stator.innerDiameter=47.8` |
| Width of back iron | 11.6 mm | `stator.yokeHeight=11.6` |
| Tooth width (equiv) | 14.8 mm | `stator.toothWidth=14.8` |
| Rotor outer diameter | 47 mm | `rotor.outerDiameter=47` |
| Air-gap length | 0.4 mm | `airgap=0.4` |
| Shaft diameter | 16 mm | `rotor.innerDiameter=16` |
| Motor length | 30.1 mm | `stator.stackLength` / `axialActiveLength=30.1` |
| No. of poles | 4 | `rotor.poleCount=4` |
| No. of stator slots | 6 | `stator.slotCount=6` |
| Magnet length (radial) | 4.35 mm | `rotor.magnetThickness=4.35` |
| Magnet height | 17.6 mm | `rotor.magnetHeight=17.6`（扩展） |
| Magnet span | 45° | `rotor.magnetSpanDeg=45` |
| Slot opening W/H | 3.23 / 0.98 mm | `stator.slotOpeningWidth/Height`（扩展） |
| Tooth height equiv | 20 mm | 仅 `meta.toothHeightEquiv_mm` 文档化 |

其它约定：

- `topology=RF`，`machineType=PMSM`，`rotorTopology=inner`，`slotShape=straight`，`skewAngle=null`
- 论文磁钢 **inset** → `rotor.magnetTopology="IPM"`（**勿**用 SPM）
- 气隙校核：`47 + 2×0.4 = 47.8` → `validate_radial` 通过

### 绕组 / 额定（meta，非 golden）

| 表 | 内容 |
| --- | --- |
| Table 9 | turns per slot = 328；1 layer；concentrated（tooth wound） |
| Table 7 | M250-35A / sintered ferrite radially magnetized |
| Table 6 | 额定约 **0.10 Nm @ 2000 rpm** |
| Table 8 | Inom = 0.21 Arms |
| Table 10 | Rs=8.9462 Ω、λpm=0.1144 Wb、E0≈47.37 Vpeak@2000 |

**turns_per_phase 假设（单层集中绕组）：**

```text
turns_per_phase = (slots / phases) * turns_per_slot
                = (6 / 3) * 328
                = 656
```

解析可改假设；几何侧仅在 analytic 骨架 / case README 写清。

## 交付路径

| 路径 | 说明 |
| --- | --- |
| `packages/geometry/src/mo_geometry/radial.py` → `creator_radial_pmsm_4p6s()` | 工厂 |
| `packages/geometry/examples/radial_pmsm_creator_4p6s_params.json` | mems 片段 |
| `..._mesh.json` / `..._geometry_summary.json` | mesh + SI GeometrySummary |
| `..._analytic_request.json` | 可拷到 `packages/solver-analytic/smoke/fixtures/` 试用的骨架（**非 golden**） |
| `tests/benchmark/cases/rf-pmsm-creator-001/` | 标杆 case（input 与工厂一致；golden 仍 pending） |

重建 creator 样例（同时重写默认 RF/AF examples，勿破坏现测）：

```bash
cd packages/geometry && source .venv/bin/activate
python -m mo_geometry.rebuild_examples
# analytic_request 不由 rebuild 覆盖；改骨架请手改或跑测试旁脚本
```

## 与默认 `radial_pmsm` demo 的区别

| | `default_radial_pmsm()` | `creator_radial_pmsm_4p6s()` |
| --- | --- | --- |
| 用途 | 包内 demo / FE 联调 | CREATOR 公开标杆 4p/6s |
| 极 / 槽 | 6 / 18 | **4 / 6** |
| 定子 OD/ID | 80 / 51 mm | **113 / 47.8 mm** |
| 转子 OD | 50 mm | **47 mm** |
| 气隙 | 0.5 mm | **0.4 mm** |
| 磁钢拓扑 | SPM | **IPM**（inset） |
| 叠长 | 25 mm | **30.1 mm** |
| examples 文件前缀 | `radial_pmsm_*` | `radial_pmsm_creator_4p6s_*`（**不**覆盖 demo） |

## 给 Mo-解析的拷贝提示

1. 几何 SI：直接用 `radial_pmsm_creator_4p6s_geometry_summary.json` 或 analytic_request 内 `geometry`。
2. 整份 SolveRequest 骨架：拷 `radial_pmsm_creator_4p6s_analytic_request.json` → `packages/solver-analytic/smoke/fixtures/`（自行命名）；或对照 case `input/`。
3. **勿**把 `meta` 当 golden；标定与 `tests/benchmark/golden/` 由解析接手。
4. case id：`rf-pmsm-creator-001`。
