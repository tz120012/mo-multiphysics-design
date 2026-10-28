# Q4+ 冒烟记录 — C2 FE（`/field` source = job-artifacts）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 15:38 Asia/Shanghai |
| 业务 tip | **`4794565`**（`feat(web): align /field to job-artifacts with explicit fixture override`） |
| tip 全 SHA | `4794565`（short；`git rev-parse --short 4794565`） |
| merge tip | **`6a32d9d`**（`Merge pull request #3 from tz120012/cursor/field-job-artifacts-source-30c0`） |
| 祖先确认 | `git merge-base --is-ancestor 4794565 HEAD` → **0**；`6a32d9d` 同为祖先 |
| 依据说明 | [Q4plus-FE-field-source](Q4plus-FE-field-source.md)（路径说明；本记录为冒烟 PASS） |
| 执行 | Mo-测试；浏览器 UI 冒烟；**仅** `docs/qa/` 落盘；**未**改业务代码；**未** push |
| 环境 | vite `http://127.0.0.1:5173`；成功样例 jobId `913d2d89-614d-43f6-943a-0a32adc4ec57` |
| 性质 | Q4+-C2 **FE 段**；后端已于 tip **`6144f91`** 关；**不代签**整关 Q4+-3 |

## 四场景实测（照抄入库）

| # | URL | 期望 / 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | `/field?jobId=913d2d89-614d-43f6-943a-0a32adc4ec57` | `source=job-artifacts` / `data-field-source=job-artifacts`；页眉含 artifacts 路径；SUCCEEDED | **PASS** |
| 2 | 同上 + `&source=fixture` | `source=job-fixture`；注记含显式 `?source=fixture`；Network **无** `/artifacts`（仅 public fixture） | **PASS** |
| 3 | `/field` 与 `/field?source=fixture` | `source=fixture` | **PASS** |
| 4 | `/field?jobId=00000000-0000-0000-0000-000000000099` | `source=job-fixture`（列表/manifest 404 后降级） | **PASS** |

**结论**：四场景全 **PASS**（对照 [Q4plus-FE-field-source](Q4plus-FE-field-source.md) 抽查表）。

## C2 判定

| ID | 结论 | 说明 |
| --- | --- | --- |
| Q4+-C2 后端 | **PASS**（既证） | tip **`6144f91`** @ **`83d2e6e`**；见 [Q4plus-冒烟记录-C1-C2-artifacts](Q4plus-冒烟记录-C1-C2-artifacts.md) |
| Q4+-C2 FE | **PASS** | tip **`4794565`** / merge **`6a32d9d`**；四场景上表 |

## 关项口径（跟踪必须）

| 项 | 写法 |
| --- | --- |
| Q4+-3 | **通过**（**产品已确认整关**；后端+FE；mems/files=Q4+-3b 后置） |
| Q3-L4 **子项** field/artifacts **FE 段** | **可关**（`source=job-artifacts` @ `4794565`） |
| Q3-L4 **整行** | **仍不可整关**（余 真 Elmer/Maxwell 磁静力学后处理等；live/AF Wasm、磁静力学 CLI shell/边界、mems API 子项已可记部分消化） |
| 禁止宣称 | **≤5% / ≤3%** 达标、**MVP 已达成** — 一律**不宣称**；**不勾 F1/F2**；**不代签** |

## 跟踪 / 清单变更

| 项 | 变更 |
| --- | --- |
| [Q4plus-冒烟清单](Q4plus-冒烟清单.md) | C2 FE 段 → **PASS**（tip **`4794565`**）；F1/F2 **不勾** |
| [Q4plus-验收跟踪](Q4plus-验收跟踪.md) | Q4+-3→**通过（后端）· FE 段测试通过 · 待产品确认整关**；Q3-L4 FE 子项可关 / 整行不可关 |

## 未做

- **未**代签整关 Q4+-3（待产品确认）。
- **未**整关 Q3-L4。
- **未**勾 F1/F2；**未**宣称 MVP；**未** push。

---

**产品确认（Mo-产品）**：同意 C2 FE 四场景 PASS + 后端已关 → Q4+-3 **通过**（整关；F5=A；`mems/files`=Q4+-3b 后置）。证据 tip **`db964d0`**；业务 **`4794565`** / merge **`6a32d9d`**。**禁勾 ≤5%/≤3%**；**不开宣称 MVP**。

---

*证据 tip：本 commit short SHA（冒烟入库 **`db964d0`**）；业务对照 `4794565` / merge `6a32d9d`。*
