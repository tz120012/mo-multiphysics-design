# Q4+ 冒烟清单（骨架）

> 依据：`docs/02-阶段任务拆解与门禁.md` § Q4+；跟踪见 [Q4plus-验收跟踪](Q4plus-验收跟踪.md)  
> 对应任务：**Q4+-6**（Q4+ 冒烟与遗留关项记录）；与 Q4+-1…Q4+-5 交付物对照  
> 执行：Mo-测试 · tip 以实测时 `git rev-parse --short HEAD` 为准  
> 范围：发布候选加固——校准计划、`:5174`、mems/artifacts·FE、live 几何/AF Wasm、磁静力学 FEM/轴向真值  
> **误差**：解析 ≤5% / FEM ≤3% 均为 **待校准**——**校准书面关闭前不得勾「≤5%/≤3% 达标」**  
> **MVP**：本清单**不开宣称 MVP 已达成**；Motor 分批签字；全关后方可议该宣称  
> **Q4+-6**：**已开闸**（Motor 确认 Q4+-3 整关后开；见 [Q4plus-验收跟踪](Q4plus-验收跟踪.md)；签字包骨架 [Q4plus-P06-签字包](Q4plus-P06-签字包.md)）；**仍不**勾 F1/F2；**不开宣称 MVP**  
> **现状**：A1/A2 **PASS**（对照 tip **`81699d3`** / `5df616d` / 产品 **`31c6597`**；记录 [Q4plus-冒烟记录-A1-A2-G3](Q4plus-冒烟记录-A1-A2-G3.md)）；**B1 PASS**（`f929dcb`；[Q4plus-冒烟记录-Q4+-2-5174-proxy](Q4plus-冒烟记录-Q4+-2-5174-proxy.md)）；C1 **PASS** / C2 **PASS（后端 + FE）**（后端 **`6144f91`** @ **`83d2e6e`**；FE tip **`4794565`** / merge **`6a32d9d`**；记录 [Q4plus-冒烟记录-C1-C2-artifacts](Q4plus-冒烟记录-C1-C2-artifacts.md)、[Q4plus-冒烟记录-C2-FE-field-source](Q4plus-冒烟记录-C2-FE-field-source.md)）；D1/D2 **PASS**（几何 `ad66ff9` / Wasm `166c319`；[Q4plus-冒烟记录-D1-D2-geometry](Q4plus-冒烟记录-D1-D2-geometry.md)）；E1/E2 **PASS**（FEM tip **`9ffa4b2`**；记录 [Q4plus-冒烟记录-E1-E2-magnetostatic](Q4plus-冒烟记录-E1-E2-magnetostatic.md)）；其余区仍待 tip；**F1/F2 禁勾**；**不开宣称 MVP**

## 状态说明

| 标记 | 含义 |
| --- | --- |
| SKIP | 业务未就绪；占位通过，不挡 CI |
| TODO | 待实现后实跑 |
| PASS / FAIL | 实跑结论（**本骨架阶段一律不用 PASS 冒充业务验收**） |

## A. 校准计划（对照 Q4+-1 / G3）

| ID | 检查项 | 通过标准（就绪后） | 现状 |
| --- | --- | --- | --- |
| Q4+-A1 | G3 校准计划正式稿入库 | 含 golden 路径与关闭条件；可指向 docs | **PASS**（tip **`81699d3`** / `5df616d` / 产品 `31c6597`；§2 golden 表 + §4 关闭条件 + §6 四项确认；见 [Q4plus-冒烟记录-A1-A2-G3](Q4plus-冒烟记录-A1-A2-G3.md)） |
| Q4+-A2 | 关闭条件可跟踪 | G3/Q2-L4 关闭条件可对照；**仍禁勾 ≤5%/≤3%** | **PASS**（§4.1 文档债可关；§4.2/§4.3 数值须标定报告；文中明确禁勾 ≤5%/≤3%；tip **`81699d3`**） |

## B. compose `:5174`（对照 Q4+-2）

| ID | 检查项 | 通过标准（就绪后） | 现状 |
| --- | --- | --- | --- |
| Q4+-B1 | nginx→host 代理可测 | `:5174` 可通或书面不可行+替代路径备案 | **PASS**（交测 tip **`f929dcb`**；`:5174/`/`/health`/`/api/v1/health`→200；db/redis ok；见 [Q4plus-冒烟记录-Q4+-2-5174-proxy](Q4plus-冒烟记录-Q4+-2-5174-proxy.md)） |

## C. mems / artifacts / FE（对照 Q4+-3）

| ID | 检查项 | 通过标准（就绪后） | 现状 |
| --- | --- | --- | --- |
| Q4+-C1 | Jobs artifacts = L4 精简单文件权威（**无**独立 mems/files；mems/files=Q4+-3b） | OpenAPI/源码注记可抽；pytest；可选 compose list/get | **PASS**（tip **`6144f91`** @ 裁决 **`83d2e6e`** / F5=A；pytest **10 passed**；关 Q3-L4「无 mems 单文件 GET」**子项**；见 [Q4plus-冒烟记录-C1-C2-artifacts](Q4plus-冒烟记录-C1-C2-artifacts.md)） |
| Q4+-C2 | artifacts / FE 对齐 | 后端注记锁定；FE 非仅 fixture（`source=job-artifacts`）可抽 | **PASS（后端 + FE）**（后端 OpenAPI/router 注记齐 @ **`6144f91`**；FE tip **`4794565`** / merge **`6a32d9d`**：四场景 `job-artifacts`/`job-fixture`/`fixture` 全 PASS；见 [Q4plus-冒烟记录-C2-FE-field-source](Q4plus-冒烟记录-C2-FE-field-source.md)） |

## D. live 几何 / AF Wasm（对照 Q4+-4）

| ID | 检查项 | 通过标准（就绪后） | 现状 |
| --- | --- | --- | --- |
| Q4+-D1 | live 几何包 | 可演示交付或明确降级说明 | **PASS**（tip **`ad66ff9`**：pytest 30；`rebuild_live_geometry`/`rebuild_examples`；AF summary 可抽；STEP/DXF 书面降级；见 [Q4plus-冒烟记录-D1-D2-geometry](Q4plus-冒烟记录-D1-D2-geometry.md)） |
| Q4+-D2 | AF Wasm 余项 | 可演示或书面降级 | **PASS**（tip **`166c319`**：`cargo test` 5；`solve_json`+`axial_pmsm_request.json` 有限 T/E；`meta.solver=axial_planes`/`wasm=true`；几何 summary 可喂；**禁勾 ≤5%**；见记录） |

## E. 磁静力学 FEM / 轴向真值（对照 Q4+-5）

| ID | 检查项 | 通过标准（就绪后） | 现状 |
| --- | --- | --- | --- |
| Q4+-E1 | dry-run / 真求解边界文档 | 边界书面化；heat-proxy ≠ 磁静力学 | **PASS**（tip **`9ffa4b2`**；边界稿 [Q4plus-5-磁静力学与轴向真值](../drafts/Q4plus-5-磁静力学与轴向真值.md)；见 [Q4plus-冒烟记录-E1-E2-magnetostatic](Q4plus-冒烟记录-E1-E2-magnetostatic.md)） |
| Q4+-E2 | 可冒烟壳升级 | 壳可抽查；**禁勾 ≤3%** 直至校准关闭 | **PASS**（tip **`9ffa4b2`**；`run_magnetostatic_shell.py` exit 0；`pending_calibration`；力标量 null；**禁勾 ≤3%**；见记录） |

## F. 误差门槛（强制）

| ID | 检查项 | 通过标准 | 现状 |
| --- | --- | --- | --- |
| Q4+-F1 | **解析 ≤5% 达标** | 相对标杆 ≤5% **且**校准书面关闭 | **禁止勾选直至校准关闭** |
| Q4+-F2 | **FEM ≤3% 达标** | 相对标杆 ≤3% **且**校准书面关闭 | **禁止勾选直至校准关闭** |

## G. 流程项（人工 / Motor）

| ID | 检查项 | 通过标准 | 现状 |
| --- | --- | --- | --- |
| Q4+-G1 | 遗留已转入 | Q3-L4 / Q4-校准·G3 / `:5174` / pending_calibration 见跟踪表 | **骨架 PASS**（已转入；未消化） |
| Q4+-G2 | Motor 分批签字 | 有证据后分批签；全关后方可议 MVP 已达成；**本员不代签**；**本阶段不自动授权该宣称** | **进行中**（Q4+-6 已开闸；交 [Q4plus-P06-签字包](Q4plus-P06-签字包.md) 草稿；**仍不**宣称 MVP） |

## 执行方式（骨架）

1. 各角色 tip / 交测后，Mo-测试按区实跑并改「现状」。  
2. A1/A2、B1、C1、C2（后端+FE）、D1/D2 、E1/E2 已有 PASS；其余区在对应 tip 入库前保持 TODO。  
3. 不得勾选 F1/F2；不得宣称 MVP 已达成。  
4. 证据附于 [Q4plus-验收跟踪](Q4plus-验收跟踪.md) 与分项冒烟记录（A1/A2：[Q4plus-冒烟记录-A1-A2-G3](Q4plus-冒烟记录-A1-A2-G3.md)；C1/C2 后端：[Q4plus-冒烟记录-C1-C2-artifacts](Q4plus-冒烟记录-C1-C2-artifacts.md)；C2 FE：[Q4plus-冒烟记录-C2-FE-field-source](Q4plus-冒烟记录-C2-FE-field-source.md)；D1/D2：[Q4plus-冒烟记录-D1-D2-geometry](Q4plus-冒烟记录-D1-D2-geometry.md)；E1/E2：[Q4plus-冒烟记录-E1-E2-magnetostatic](Q4plus-冒烟记录-E1-E2-magnetostatic.md)）。

## 相关链接

- [Q4plus-验收跟踪](Q4plus-验收跟踪.md)
- [Q4plus-冒烟记录-A1-A2-G3](Q4plus-冒烟记录-A1-A2-G3.md)
- [Q4plus-冒烟记录-C1-C2-artifacts](Q4plus-冒烟记录-C1-C2-artifacts.md)
- [Q4plus-冒烟记录-C2-FE-field-source](Q4plus-冒烟记录-C2-FE-field-source.md)
- [Q4plus-冒烟记录-D1-D2-geometry](Q4plus-冒烟记录-D1-D2-geometry.md)
- [Q4plus-冒烟记录-E1-E2-magnetostatic](Q4plus-冒烟记录-E1-E2-magnetostatic.md)
- [G3-校准计划](G3-校准计划.md)
- [Q4-签字记录](Q4-签字记录.md)
- [Q4-P11-签字包](Q4-P11-签字包.md) §4
- [02-阶段任务拆解与门禁](../02-阶段任务拆解与门禁.md) § Q4+

---

*Mo-测试填实中；Q4+-6 已开闸（Motor）；A1/A2 已关文档债；B1/C1 PASS；C2 后端+FE PASS（tip `4794565`；Motor 已确认 Q4+-3 整关）；D1/D2 已补记录；E1/E2 磁静力学壳已 PASS（禁勾 ≤3%）；禁勾 ≤5%/≤3%；不开 MVP；不勾 F1/F2。*
