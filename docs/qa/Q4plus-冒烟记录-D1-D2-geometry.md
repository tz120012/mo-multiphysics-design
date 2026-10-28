# Q4+ 冒烟记录 — D1/D2（live 几何 + AF Wasm）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 15:28 Asia/Shanghai |
| 几何 tip | **`ad66ff9`**（`feat(geometry): Q4+-4 AF summary align + live rebuild`） |
| AF Wasm tip | **`166c319`**（`feat(wasm): Q4+-4 AF+PMSM axial_planes demo path`） |
| 仓库 HEAD（实测时） | **`3646c94`**（含 `ad66ff9` / `166c319` 祖先） |
| 执行 | Mo-测试 |
| 范围 | **Q4+-D1** live 几何包抽测 + **Q4+-D2** Wasm AF+PMSM fixture 可演示；**不**勾 F1/F2；**不开宣称 MVP**；**不代签**产品/Motor |
| 建议跟踪 | Q4+-4 → **待产品确认**（测试证据已齐；不代签） |

## 环境

- `git merge-base --is-ancestor ad66ff9 HEAD` → exit 0。
- `git merge-base --is-ancestor 166c319 HEAD` → exit 0。
- 工作目录：`/workspace/mo-platform`。
- 未改 `packages/` / `apps/` 业务代码；本记录与跟踪/清单更新仅 `docs/qa`。
- 自称「pytest 30 passed」经抽测核实（见下），非盲信。

## D1 — live 几何包（tip `ad66ff9`）

### 抽测命令与结果

| # | 命令 | exit | 关键断言 / 结果 |
| --- | --- | --- | --- |
| 1 | `cd packages/geometry && source .venv/bin/activate && pip install -e ".[dev]" -q && pytest -v` | **0** | **30 passed**（含 `test_rebuild_live_geometry_rf_and_af`、`test_af_pmsm_summary_*`、`test_rebuild_examples_writes_af_fields`、`test_examples_match_export_spotcheck` 等） |
| 2 | `python -m mo_geometry.rebuild_examples` | **0** | 重写 `examples/` 径向/轴向 params、mesh、geometry_summary、pipeline_entry |
| 3 | `python scripts/rebuild_examples.py` | **0** | 等价入口可跑通 |
| 4 | CLI：`export_geometry_summary(default_axial_af_pmsm())` + `rebuild_live_geometry` | **0** | AF summary 含 `outer_radius_m=0.06`、`inner_radius_m=0.02`、`disk_thickness_m=0.008`、`disk_count=3`、`n_planes=4`、`stack_length_m=0.008`、`poles=10`；`disk_thickness_m == stack_length_m`；live 含 `params` / `meshDescriptor` / `geometrySummary` / `pipelineEntry` |

### STEP / DXF 降级依据

书面 OK（**不要求**真导出全绿）：

- [`docs/drafts/几何-Q4plus-live与降级.md`](../drafts/几何-Q4plus-live与降级.md) §2：本阶段明确降级；未捆绑 CadQuery/OCC；可演示路径为 mesh descriptor + GeometrySummary + pipeline_entry。
- [`packages/geometry/README.md`](../../packages/geometry/README.md)：STEP/DXF 行标注 **Q4+ 明确降级**。

**D1 结论：PASS**（live API + examples 可重建 + AF summary 字段可抽查；STEP/DXF 书面降级）。

## D2 — AF Wasm 余项（tip `166c319`）

### 抽测命令与结果

| # | 命令 | exit | 关键断言 / 结果 |
| --- | --- | --- | --- |
| 1 | `cd packages/solver-analytic-wasm && cargo test` | **0** | **5 passed**（含 `af_pmsm_fixture_finite`、`af_non_pmsm_clear_error`、`pmsm_fixture_finite`、`acim_fixture_finite`、`bad_json_error_shape`） |
| 2 | Node：`initSync` + `solve_json(fixtures/axial_pmsm_request.json)`（`pkg/`） | **0** | `torque_nm≈2.614`、`back_emf_v_peak≈27.371` **有限非 NaN**；`meta.solver=axial_planes`；`meta.wasm=true`；`meta.mock=false` |
| 3 | 同上，geometry 叠入 `examples/axial_af_pmsm_rfmr_geometry_summary.json`（tip `ad66ff9` 字段） | **0** | 有限 T/E；`meta.solver=axial_planes`；`meta.wasm=true`——**几何 summary 可喂本路径** |

### 口径（强制）

- 数值以 **Python** `packages/solver-analytic/axial_planes` 为金标；Wasm 为可演示 stub。
- 说明见 [`docs/drafts/Q4+-4-AF-Wasm.md`](../drafts/Q4+-4-AF-Wasm.md)。
- **禁勾 ≤5%**；`meta.note` 亦标明 not calibrated to ≤5%。
- **不开宣称 MVP**。
- D2 标为 **通过（Wasm AF+PMSM fixture 可演示）**——**不是**数值验收关闭，**不是**「精度已交付」。

**D2 结论：PASS**（Wasm AF+PMSM fixture 可演示；禁勾 ≤5%；不代签）。

## 未做 / 禁止宣称

- **未**勾选 Q4+-F1（解析 ≤5%）/ Q4+-F2（FEM ≤3%）。
- **未**开宣称 MVP 已达成。
- **未**代签产品/Motor；跟踪仅建议 **待产品确认**。
- **未**改业务代码；**未** push。
- **未**动 A1/A2、B、C、E 并行区段落以外的无关改动。

## 跟踪 / 清单变更

| 项 | 变更 |
| --- | --- |
| [Q4plus-验收跟踪](Q4plus-验收跟踪.md) | Q4+-4 → **待产品确认**；备注 D1/D2 PASS 证据 tip `ad66ff9`/`166c319`；**禁勾 ≤5%**；**不开宣称 MVP**；不代签 |
| [Q4plus-冒烟清单](Q4plus-冒烟清单.md) | Q4+-D1 / Q4+-D2 → **PASS**；F1/F2 **不勾** |
| Q4+-6 | 仍未全开；注明 D1/D2 已补记录 |

## 结论

| ID | 结论 |
| --- | --- |
| Q4+-D1 | **PASS**（live 几何 / CLI / rebuild；STEP/DXF 书面降级） |
| Q4+-D2 | **PASS**（Wasm AF+PMSM fixture；禁勾 ≤5%） |
| Q4+-4 跟踪 | **待产品确认**（测试不代签） |
| Q4+-F1 / F2 | **禁止勾选** |
| MVP | **不开宣称** |

证据 tip：本记录入库 commit 的 short SHA（见跟踪变更日志）。

---

*Mo-测试 · 仅 docs/qa。*
