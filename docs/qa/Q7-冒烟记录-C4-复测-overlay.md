# Q7 冒烟记录 — C4 复测 PASS（overlay 已修 · 对照 FAIL tip `646e1bf`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-29 20:27 Asia/Shanghai |
| 对照 FAIL tip | **`646e1bf`**（[Q7-冒烟记录-C1-C5-浏览器-0ee6fd3](Q7-冒烟记录-C1-C5-浏览器-0ee6fd3.md)；C4 FAIL：代理网络不可达 → rebuild 无 HTTP 状态） |
| 环境 tip | merge tip **`0ee6fd3`**；FE tip **`7ba2e5e`**；overlay 已修（运维 `27707ee` 等） |
| compose | web **`http://127.0.0.1:5174/`**；api **`:8000`**（同源 `/api` 代理） |
| 登录 | demo |
| 执行 | Mo-测试；浏览器复测 **C4**；**仅** `docs/qa/`（含 artifacts/q7-c4-retest）；**未**改业务代码 |
| 清单 | [Q7-冒烟清单](Q7-冒烟清单.md) **Q7-C4** |
| 总评 | **Q7-C4 = PASS（浏览器复测）**；C1/C2/C3/C5 沿用 **`646e1bf` PASS**；**C1…C5 浏览器均 PASS**；**整关待产品/Motor 确认 · 不代关**；**未勾**建模完成 / Maxwell 全功能 / MVP / ≤5% / ≤3% / 扩 F1/F2 |

## 环境与会话

| 证据 | 结果 |
| --- | --- |
| overlay | 已修；经 `:5174/api` 代理可达 |
| rebuild | `POST :5174/api/v1/geometry/rebuild` → **HTTP 200** |
| paramsHash | `2585dae9…` → `6f06165980e93c39` |
| 槽 / prims | 槽 **18→12**；prims **45→33** |
| HUD / 视口 | hudDims 更新；视口槽腔变疏 + role 上色 |
| modelingComplete | **false**；横幅/HUD「非建模完成」；**未勾建模完成** |
| 截图目录 | [artifacts/q7-c4-retest/](artifacts/q7-c4-retest/)（`before-slot18.jpg`、`after-slot12.jpg`） |

## 结论（C4）

| ID | 结果 |
| --- | --- |
| Q7-C4 | **PASS（浏览器复测）** rebuild **HTTP 200**；paramsHash 更新；槽 18→12；prims 45→33；hudDims/视口可见更新；modelingComplete=false；**未勾建模完成** |

> **对照 FAIL（`646e1bf`）**：当时经 `:5174/api` 代理超时/无响应（Docker DNS）；槽 18→12 rebuild **无 HTTP 状态**；视口/HUD 仍 18。本复测 overlay 已修，代理可达，根因（运行态代理/环境）已消。

## before / after

| 维度 | before（槽 18） | after（槽 12 · rebuild 200） |
| --- | --- | --- |
| 槽数 | **18** | **12** |
| prims | **45** | **33** |
| paramsHash | `2585dae9…` | `6f06165980e93c39` |
| rebuild | —（对照 FAIL 无 HTTP） | **HTTP 200** |
| 视口 | 槽腔较密 | 槽腔变疏 + role 上色 |
| HUD | — | hudDims 更新；「非建模完成」 |
| modelingComplete | — | **false**；**未勾** |
| 截图 | [before-slot18.jpg](artifacts/q7-c4-retest/before-slot18.jpg) | [after-slot12.jpg](artifacts/q7-c4-retest/after-slot12.jpg) |

## 与 FAIL 对照

| 维度 | FAIL @ `646e1bf` | 本复测（overlay 已修） |
| --- | --- | --- |
| 代理 | `:5174/api` 超时/无响应 | 可达 |
| rebuild | **无 HTTP 状态** | **HTTP 200** |
| 视口/HUD | 仍槽 **18** | 槽 **12**；hudDims 更新；槽腔变疏 |
| paramsHash | — | `2585dae9…`→`6f06165980e93c39` |
| 结论 | **C4 FAIL 挡关** | **C4 PASS（浏览器复测）** |

## 沿用项（本轮仅补 C4）

| ID | 结果 | 依据 |
| --- | --- | --- |
| Q7-C1 | **PASS（浏览器）** | tip **`646e1bf`** / [原记录](Q7-冒烟记录-C1-C5-浏览器-0ee6fd3.md) |
| Q7-C2 | **PASS（浏览器）** | 同上 |
| Q7-C3 | **PASS（浏览器）** | 同上 |
| Q7-C5 | **PASS（浏览器）** | 同上 |

## 禁令确认

| 项 | 本记录 |
| --- | --- |
| 建模完成 | **未勾**（modelingComplete=false；横幅/HUD「非建模完成」） |
| Maxwell 全功能 / MVP / 重开 v1.0.0 | **未宣称** / **未打 tag** |
| 整机 ≤3% / ≤5% / 外推 F1/F2 | **未勾** / **未外推** |
| Q7-C1…C5 浏览器 | **均 PASS**；**整关待产品/Motor 确认 · 不代关** |
| 产品项 Q7-1…4 / Q7-6 Motor 签字 | **不代关** / **不代签** |
| 业务代码 | **未改** `apps/` |

## 相关链接

- [Q7-冒烟清单](Q7-冒烟清单.md)
- [Q7-验收跟踪](Q7-验收跟踪.md)
- [Q7-冒烟框架说明](Q7-冒烟框架说明.md)
- [Q7-冒烟记录-C1-C5-浏览器-0ee6fd3](Q7-冒烟记录-C1-C5-浏览器-0ee6fd3.md)（对照 FAIL tip **`646e1bf`**）
- 截图：[artifacts/q7-c4-retest/](artifacts/q7-c4-retest/)
- FE **`7ba2e5e`** / merge **`0ee6fd3`**；FAIL 证据 tip **`646e1bf`**

---

*Mo-测试 · C4 复测 · overlay 已修 · 对照 FAIL `646e1bf` · FE `7ba2e5e` / merge `0ee6fd3` · 2026-10-29 20:27 Asia/Shanghai · **C4 PASS** · C1…C5 浏览器均 PASS · **整关不代关** · 禁勾建模完成/Maxwell 全功能/MVP/≤3%/≤5%/扩 F1/F2*
