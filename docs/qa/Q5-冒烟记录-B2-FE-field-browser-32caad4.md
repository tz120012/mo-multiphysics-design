# Q5 冒烟记录 — FE `/field` 浏览器目视补测（@ `32caad4` · Vite `:5176`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 18:52 Asia/Shanghai |
| 业务 tip | **`32caad4`**（PR #5 open；worktree `/tmp/mo-fe-32caad4`） |
| 对照源码抽测 | [B2-FE-field-32caad4](Q5-冒烟记录-B2-FE-field-32caad4.md)（证据 tip **`0505d72`**） |
| 执行 | Mo-测试 · computerUse 目视；**未**改业务代码；仅 `docs/qa/` |
| 性质 | 补齐源码抽测「需主代理 computerUse」缺口；**不代关** B2/L4 整行；**禁勾 F2**；**不开宣称 MVP** |

## 环境

| 证据 | 结果 |
| --- | --- |
| Vite | `http://127.0.0.1:5176` @ tip **`32caad4`**（非 `:5173` 旧 web） |
| 登录 | `/field` 先重定向演示登录；账号框已是 engineer；点「登录」后进场量页 |
| 侧栏 | **无** jobId 输入控件（无 input/textarea/select；链仅工程/工作区/解析/轴向/场量/驱动/对比） |

## 目视结果

| # | URL / 项 | 可见文案 | 结论 |
| --- | --- | --- | --- |
| 1 | `/field` | 侧栏「场量 · 精简可视化」；`data-field-source=fixture`；副文案含 `source=fixture` · public fixture；说明 dry-run 未带 jobId；面板标题 **「heat-proxy / 非磁静力学真值」**；徽章 **pending_calibration**（未见单独「未校准」字样）；equationMode=未标注；magnetostaticPathReady=—；正文写明不是磁静力学真值；**未见** axialForceN / magneticEnergyJ / 「磁静力学后处理」 | **PASS**：fixture、非 MS 真值口径、pending 可见 |
| 2 | `/field?source=fixture` | 同上；来源仍 `source=fixture`（非 job-fixture）；多一句「显式 ?source=fixture」；标题仍 heat-proxy；无轴向力/磁能/「磁静力学后处理」 | **PASS**：显式 fixture；非 MS 真值 |
| 3 | magnetostatic job-artifacts | 页上**无** jobId 控件可喂；public fixture 文案写明未带 jobId | **停测 · 不记 PASS**（无真 magnetostatic jobId 可喂 UI） |
| 4 | heat-proxy 标题 | 两页标题均为「heat-proxy / 非磁静力学真值」；全文无「磁静力学后处理」 | **PASS**：标题不是「磁静力学后处理」 |

## 总评

- **fixture 路径目视：PASS**（与源码抽测一致）。
- **magnetostatic job-artifacts 真人 UI：未完成**（缺 jobId 控件 + 缺含 `equationMode=magnetostatic` 的可喂 artifacts）；与源码记录「缺口」一致；**不记 PASS**。
- **不代关** B2 / Q3-L4 整行；**未勾 F2**；未宣称 ≤3%/MVP。

## 禁令

| 项 | 本记录 |
| --- | --- |
| F2 / ≤3% | **未勾** / **未宣称** |
| MVP / tag | **未宣称** / **未打** |
| B2 / L4 整行 | **不代关**（仍后置 Q5-4） |

## 相关

- 源码四场景：[B2-FE-field-32caad4](Q5-冒烟记录-B2-FE-field-32caad4.md) · tip `0505d72`
- FEM B1 · `797ce67`；API B1 · `e3074b9`

---

*Mo-测试 · FE `/field` 浏览器目视 · 隔离仅 `/workspace/mo-platform`。*
