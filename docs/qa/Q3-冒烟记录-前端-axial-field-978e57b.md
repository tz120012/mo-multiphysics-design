# Q3 冒烟记录 — 前端 tip `978e57b`（/axial + /field 壳）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:51 Asia/Shanghai |
| 指派 tip | **`978e57b`**（`feat(web): Q3-2 axial PMSM workflow shell + Q3-6 field slice mock`） |
| 仓库 HEAD（入库时） | `4cb45c4`（`978e57b` 为 HEAD 祖先） |
| 执行 | Mo-测试执行员（**浏览器实测结论照抄入库**） |
| 范围 | `/axial`、`/field` 工作流壳；`/analytic` 未打挂（不参与壳否决）；**不**宣称解析 ≤5% / FEM ≤3% |
| 壳总评 | **PASS** |

## 环境

- `git merge-base --is-ancestor 978e57b HEAD` → exit 0。
- 未改 `apps/` 业务代码；本记录仅 `docs/qa/`。

## 浏览器实测（照抄）

### /axial — PASS

| 项 | 实测 |
| --- | --- |
| 几何 | 静态 mesh 来自 `pipeline_entry`；mesh=axial · **35 prims**（非 live 包） |
| AF | path=`sync`，solver=`axial_planes`，mock=`false`；T=**2.614** Nm（非≈2.33，记加分未满分，**不否决壳**）；E=**27.37** V；横幅仍写 AF 降级 sync→fixture / Wasm AF 未落地；本次实际 **sync HTTP** |
| FEM | `femEntryHint` **0.1.0-q3-hint** · **无网格** |

### /field — PASS

| 项 | 实测 |
| --- | --- |
| dry-run | `MANIFEST.SCALARS`、`SCALARS.JSON`（fem-scalars-v0）、`slice.gltf`、`preview.png` |
| job | **succeeded**；**非**真 Elmer |

### /analytic — 未打挂（不参与壳否决）

| 项 | 实测 |
| --- | --- |
| path | `wasm`，mec，T≈**4.086** |

## 已知缺口（不否决）

- live 几何包
- AF Wasm
- 真 Elmer
- Jobs 常驻未接

## 未做 / 禁止宣称

- **未**勾选或宣称解析相对标杆 **≤5%** / FEM **≤3%**（仍待校准）。
- **未**以壳 PASS 冒充真 Elmer / live 几何 / AF Wasm 闭环。
- **未**改 `apps/`；本记录仅文档。

## 跟踪变更

| 项 | 变更 |
| --- | --- |
| Q3-P02 前端侧 | **待测 → 通过（壳）**（tip `978e57b`；/axial） |
| Q3-P02 整体 | **通过（几何）+ 通过（壳）**（几何 tip `1bd8b51` 已过；前端壳本轮过） |
| Q3-P06 | **待测 → 通过（壳）**（tip `978e57b`；/field 切片 mock） |
| 已知缺口 | 记入备注（live 几何 / AF Wasm / 真 Elmer / Jobs 常驻）；**不否决** |
| P01/P03–P05/P07 | 本轮不改 |

## 结论

| 项 | 结论 |
| --- | --- |
| 前端 tip `978e57b` 壳总评 | **PASS** |
| /axial | **PASS** |
| /field | **PASS** |
| /analytic | 未打挂（不参与壳否决） |
| 对标 ≤5%/≤3% | **未宣称**（禁止） |
