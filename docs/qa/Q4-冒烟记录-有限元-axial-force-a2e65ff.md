# Q4 冒烟记录 — 有限元 tip `a2e65ff`（Q4-P08 轴向磁拉力占位壳）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:36 Asia/Shanghai |
| 指派 tip | **`a2e65ff`**（`feat(fem): Q4-8 axial-force placeholder shell smoke for P08`） |
| tip 全 SHA | `a2e65ff`（短；祖先核验见下） |
| 祖先确认 | `git merge-base --is-ancestor a2e65ff HEAD` → **0**（是祖先） |
| 仓库 HEAD（实测时） | **`9a377e9`**（`docs(qa): P08→待测（占位壳 a2e65ff）`；含 tip） |
| 执行 | Mo-测试；仅 `docs/qa/`；**未**改业务代码 |
| 入口 | **CLI shell**（`packages/solver-fem/smoke/run_axial_force_shell.py`）；**非** UI 专项报告全量 |
| 范围 | Q4-P08 轴向单边磁拉力与变形评估占位壳；**不**宣称 FEM ≤3% / 解析 ≤5%；**不开宣称 MVP**；heat-proxy ≠ 磁静力学验收 |

## 环境

- `git merge-base --is-ancestor a2e65ff HEAD` → exit 0。
- 工作目录：`/workspace/mo-platform`。
- 未改 `packages/` / `apps/` 业务代码；本记录与跟踪/清单更新仅 `docs/qa`。
- 交测 tip 叠 FEM 契约 **`864ec20`**（跟踪备注已记）；本轮只跑 shell 冒烟。

## 必跑命令结果（照实）

```bash
cd /workspace/mo-platform
python3 packages/solver-fem/smoke/run_axial_force_shell.py
# EXIT=0
```

| 项 | 值 |
| --- | --- |
| 入口 | `python3 packages/solver-fem/smoke/run_axial_force_shell.py` |
| exit | **0** |
| stderr / 首行 | `Q4-8 axial-force shell smoke OK (pending_calibration)` |
| 判定 | **PASS**（占位壳 / CLI shell；`pending_calibration`；轴向标量 null） |

### stdout 关键字段（照实）

| 字段 | 值 |
| --- | --- |
| `schemaVersion` | `axial-force-shell-v0` |
| `pending_calibration`（顶层） | **`true`** |
| `reportDraft` | `docs/drafts/Q4-8-large磁拉力.md` |
| `fixture` | `packages/solver-fem/fixtures/q4_axial_force_placeholders.json` |
| `resultRef` | `solver/fem/jobs/00000000-0000-4000-8000-0000000000q48/manifest.json` |
| `scalars.axialForceN` | **`null`** |
| `scalars.bearingLoadN` | **`null`** |
| `scalars.deflectionHintMm` | **`null`** |
| `scalars.pending_calibration` | **`true`** |
| `scalars.dryRun` | `true` |
| `scalars.templateId` | `af_pmsm_3d` |
| `notes` | `placeholder special-report shell; magnetostatics deferred; do NOT claim FEM ≤3%` |

### stdout 关键片段

```json
{
  "schemaVersion": "axial-force-shell-v0",
  "pending_calibration": true,
  "reportDraft": "docs/drafts/Q4-8-large磁拉力.md",
  "fixture": "packages/solver-fem/fixtures/q4_axial_force_placeholders.json",
  "resultRef": "solver/fem/jobs/00000000-0000-4000-8000-0000000000q48/manifest.json",
  "scalars": {
    "axialForceN": null,
    "bearingLoadN": null,
    "deflectionHintMm": null,
    "pending_calibration": true,
    "dryRun": true,
    "templateId": "af_pmsm_3d"
  },
  "notes": "placeholder special-report shell; magnetostatics deferred; do NOT claim FEM ≤3%"
}
```

### `pending_calibration` / 轴向标量

- 顶层与 `scalars` 均出现 **`pending_calibration: true`**。
- 轴向相关标量 **`axialForceN` / `bearingLoadN` / `deflectionHintMm` 均为 `null`**（占位；无磁静力学真值）。
- **已注明；禁止据此勾选或宣称 FEM ≤3%（及解析 ≤5%）达标。**

## 未做 / 禁止宣称

- **未**勾选或宣称 FEM 相对标杆 **≤3%** / 解析 **≤5%**（`pending_calibration: true`；仍待校准书面关闭）。
- **未**做磁静力学数值验收；heat-proxy ≠ 磁静力学验收。
- **未**测前端专项报告 UI 全量；本轮仅为 **CLI shell** 占位冒烟。
- **未**开宣称 MVP；**未**代签 Q4-P11。
- **未**改 `packages/` / `apps/` 业务代码。

## 跟踪 / 清单变更

| 项 | 变更 |
| --- | --- |
| Q4-P08 | **待测（占位壳）→ 通过（CLI shell / pending_calibration）**（证据 @ `a2e65ff`；轴向标量 null；禁勾 ≤3%） |
| P01–P04 / P06 / P07 / P09 / P10 | 维持 **通过**（本轮不改、勿冲） |
| P05 | 维持 **进行中** |
| P11 | 维持 **未开始**（等 P05） |
| 清单 Q4-D2 | **SKIP → PASS**（注明 `pending_calibration` / 轴向标量 null；CLI shell） |
| 清单 Q4-G2 | 维持 **禁止勾选直至校准关闭**（本轮**未**勾 ≤3%） |

## 结论

| 项 | 结论 |
| --- | --- |
| tip `a2e65ff` axial-force shell CLI | **PASS**（exit 0） |
| `pending_calibration` | **true**（顶层 + scalars） |
| 轴向标量 `axialForceN` 等 | **null** |
| 对标 ≤3% / ≤5% | **未宣称**（禁止） |
| MVP | **未宣称** |
| 产品项 P08 | **通过（CLI shell / pending_calibration）** |
