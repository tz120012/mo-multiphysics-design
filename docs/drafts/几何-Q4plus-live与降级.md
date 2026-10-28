# 几何 Q4+：live 可演示路径与明确降级

> 对照：`docs/qa/Q4plus-冒烟清单.md` **D**（Q4+-D1 / Q4+-D2）；任务 Motor **Q4+-4**。  
> 维护：Mo-几何 · 仅 `packages/geometry`。  
> **禁止** MVP / ≤5% / ≤3% 等精度或完成度宣称句。

## 1. live 已交付（Q4+-D1）

本包提供 **Python live 路径**（参数 → 可演示导出），可重生成 `examples/`：

| API / 脚本 | 作用 |
| --- | --- |
| `export_geometry_summary(params)` | → 解析 `GeometrySummary`（snake_case + SI 米；AF 含半径/盘厚/盘数/`n_planes` 等） |
| `export_axial_pipeline_entry(params)` | AF-PMSM 串联包（含 `analyticSolveStub.geometry` = summary） |
| `rebuild_live_geometry(params)` | 一次返回 `{params, meshDescriptor, geometrySummary[, pipelineEntry]}` |
| `python -m mo_geometry.rebuild_examples` | 从 `default_*` 重写 `packages/geometry/examples/` |

**与 FE 静态拷贝的关系：** `apps/web/public/geometry/*pipeline_entry.json` 等仍可由 FE 维护为联调快照；浏览器内 remesh **不**由本包改 `apps/web`——FE 可调后端调用上述 API，或照抄 descriptor / 用本包 examples 同步。几何侧 live = Python 可重生成样例 + 导出 API。

## 2. STEP / DXF：本阶段明确降级

- **未捆绑** CadQuery / OpenCascade；本包 **不**安装重型 OCC。
- Q2 曾要求 STEP/DXF 可演示，**本阶段明确降级**：发布候选以 **mesh descriptor + GeometrySummary + pipeline_entry** 为可演示几何导出。
- **后置条件（简述）**：独立 OCC/CadQuery 服务或可选 extra 落地后，再开 STEP 装配 / DXF 截面导出；不阻塞 Q4+ D 冒烟以 mesh/summary 路径关闭。

## 3. AF Wasm：契约对齐，不宣称 Wasm AF 已交付（Q4+-D2）

- 几何侧 `GeometrySummary` **已与** `solve.schema.json` / `axial_planes/geometry.py` 对齐（`outer_radius_m`、`inner_radius_m`、`disk_thickness_m`、`disk_count`、`n_planes` 默认 4、可选 `magnet_arc_ratio`），可供 **未来** Wasm AF 同契约消费。
- **当前** `packages/solver-analytic-wasm` 为 **RF-only**；AF 交互仍走 sync / Jobs。几何包 **不改** wasm 包、**不宣称** Wasm AF 已交付。

## 4. 消费要点（跨角色）

- **Mo-解析**：AF SolveRequest 可优先吃 `outer_radius_m`+`inner_radius_m`（不必再走直径 stub）；`n_planes`/`disk_thickness_m` 与 axial_planes 一致。
- **Mo-前端**：静态 `public/geometry` ≠ live；联调可 POST/调后端用 `rebuild_live_geometry` 或拷贝 examples。
- **Motor / QA**：D1 = live API + examples 可重建 **或** 本文降级说明；D2 = 几何契约对齐 + Wasm AF 未交付书面说明（本节 §3）。

---

*短文结束。细节见 `packages/geometry/README.md`、`examples/README.md`、`docs/drafts/几何范围.md` Q4+ 旁注。*
