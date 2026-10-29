# Q7 冒烟记录 — C1…C5 浏览器目视（merge tip `0ee6fd3` / FE `7ba2e5e`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-29 20:21 Asia/Shanghai |
| 环境 tip | merge tip **`0ee6fd3`**（`merge(web): Q7-1…4 PR #8 tip 7ba2e5e — 材料/激励/后处理/视口`）；FE tip **`7ba2e5e`** |
| compose | web **`http://127.0.0.1:5174/`**；api **`:8000`**（同源 `/api` 代理） |
| 登录 | demo（顶栏已登录；直连 `:8000` login **200**） |
| 执行 | Mo-测试；浏览器目视已完成；**仅** `docs/qa/`（含 artifacts 截图）；**未**改业务代码 |
| 清单 | [Q7-冒烟清单](Q7-冒烟清单.md) **Q7-C1…C5** |
| 总评 | **C1/C2/C3/C5 = PASS（浏览器）**；**C4 = FAIL（浏览器）**（代理网络不可达 → rebuild 无 HTTP 状态）→ **C4 挡关**；**整关未放行**；产品/Motor **不代关**；**未勾**建模完成 / Maxwell 全功能 / MVP / ≤5% / ≤3% / 扩 F1/F2 |

## 环境与会话

| 证据 | 结果 |
| --- | --- |
| 登录 | demo；顶栏已登录；直连 `:8000` login **200** |
| 宿主直连 api | `:8000/health` 与 `/api/v1/health` → **200** |
| 经 `:5174/api` 代理 | 冒烟时 **超时/无响应**（Docker 内置 DNS `127.0.0.11` Connection refused；容器间 web→api 不通） |
| 材料目录 GET | 经代理失败 → UI 回退种子清单（诚实文案） |
| 截图目录 | [artifacts/q7-c1-c5-browser/](artifacts/q7-c1-c5-browser/)（11 张 png；**勿删**） |

## 结论表（照抄 · 勿美化）

| ID | 结果 |
| --- | --- |
| Q7-C1 | **PASS（浏览器）** 材料下拉 mat-*（steel m19/50ww470；ndfeb n42/n35；copper/coil-al）；检视区域→id；文案「材料目录暂不可达…不回退 demo 别名」；无 demo-* / 裸 Cu 请求；求解按钮禁用因无 live geometrySummary（fixture 几何红线），**非**材料 id 失败 |
| Q7-C2 | **PASS（浏览器）** 步骤名「激励」；speed_rpm 3000→1800 同壳可读可改；drive 草稿本壳；无 /excitation/* |
| Q7-C3 | **PASS（浏览器）** 无 job 诚实文案「未绑定 FEM job…不宣称误差达标」；「在本壳查看场图」仍 `/workspace?step=post`；artifacts/job 超时后诚实降级 fixture + heat-proxy≠磁静力学 + pending_calibration；**未勾**精度/MS 整机 |
| Q7-C4 | **FAIL（浏览器）** 槽 18→12 发 `POST .../geometry/rebuild` **无 HTTP 状态**（代理网络不可达）；视口/HUD 仍槽 18；paramsHash —；dataSource=degraded；有「非建模完成」横幅；**未勾建模完成**。根因口径：**运行态 web→api 代理 / Docker DNS 环境**，非材料别名回潮 |
| Q7-C5 | **PASS（浏览器）** 网格「非网格生成完成」；无 MVP/≤5%/≤3% 越权 |

## 分项证据

### Q7-C1 材料区域→`mat-*` — **PASS（浏览器）**

- 材料下拉可见 `mat-*`：steel m19 / 50ww470；ndfeb n42 / n35；copper / coil-al。
- 检视区域→id；文案：「材料目录暂不可达…不回退 demo 别名」。
- **无** `demo-*` / 裸 `Cu` 请求。
- 求解按钮禁用：因无 live `geometrySummary`（fixture 几何红线），**非**材料 id 失败。
- 截图：[c1-materials-steel-dropdown.png](artifacts/q7-c1-c5-browser/c1-materials-steel-dropdown.png)、[c1-materials-inspect-ids.png](artifacts/q7-c1-c5-browser/c1-materials-inspect-ids.png)、[c1-solve-no-live-geometry.png](artifacts/q7-c1-c5-browser/c1-solve-no-live-geometry.png)

### Q7-C2 激励同壳可读可改 — **PASS（浏览器）**

- 步骤名「激励」。
- `speed_rpm` 3000→1800 同壳可读可改；drive 草稿本壳。
- **无** `/excitation/*`。
- 截图：[c2-excitation-speed1800.png](artifacts/q7-c1-c5-browser/c2-excitation-speed1800.png)

### Q7-C3 后处理同壳 + 降级明示 — **PASS（浏览器）**

- 无 job 诚实文案：「未绑定 FEM job…不宣称误差达标」。
- 「在本壳查看场图」仍 `/workspace?step=post`。
- artifacts/job 超时后诚实降级：fixture + heat-proxy≠磁静力学 + `pending_calibration`。
- **未勾**精度 / MS 整机。
- 截图：[c3-post-no-job.png](artifacts/q7-c1-c5-browser/c3-post-no-job.png)、[c3-field-same-shell-loading.png](artifacts/q7-c1-c5-browser/c3-field-same-shell-loading.png)、[c3-field-job-timeout.png](artifacts/q7-c1-c5-browser/c3-field-job-timeout.png)、[c3-field-heat-proxy-degrade.png](artifacts/q7-c1-c5-browser/c3-field-heat-proxy-degrade.png)

### Q7-C4 参数化 3D 体感 — **FAIL（挡关）**

- 槽 **18→12** 发 `POST .../geometry/rebuild` → **无 HTTP 状态**（代理网络不可达）。
- 视口/HUD 仍槽 **18**；`paramsHash` —；`dataSource=degraded`。
- 有「非建模完成」横幅；**未勾建模完成**。
- **根因口径**：**运行态 web→api 代理 / Docker DNS 环境**，**非**材料别名回潮。
- 截图：[c4-geometry-before-slots18.png](artifacts/q7-c1-c5-browser/c4-geometry-before-slots18.png)、[c4-geometry-after-slots12-rebuilding.png](artifacts/q7-c1-c5-browser/c4-geometry-after-slots12-rebuilding.png)
- **结论：C4 FAIL → 挡关；有 FAIL 不得整关放行。** 待运维修 overlay 后可复测 C4。

### Q7-C5 表述边界 — **PASS（浏览器）**

- 网格「非网格生成完成」。
- **无** MVP / ≤5% / ≤3% 越权。
- 截图：[c5-mesh-readonly.png](artifacts/q7-c1-c5-browser/c5-mesh-readonly.png)
- 本记录 **未勾** 建模完成 / Maxwell 全功能 / MVP / ≤5% / ≤3% / 扩 F1/F2。

## 阻塞（挡关）

| 阻塞 | 说明 | 影响 |
| --- | --- | --- |
| web→api 代理 / Docker DNS | 页面经 `:5174/api` 超时/无响应；Docker DNS `127.0.0.11` Connection refused；容器间 web→api 不通。宿主直连 `:8000` 健康 **200** | rebuild / 材料目录等经代理失败 |
| **C4 挡关** | 槽 18→12 rebuild **无 HTTP 状态**；视口/HUD 仍 18 | **整关未放行**；产品 Q7-1…4 / Q7-6 **不代关** |

## 环境注记（代理）

- **宿主直连**：`:8000/health`、`/api/v1/health` → **200**。
- **经 compose web 代理**：冒烟时超时/无响应（Docker 内置 DNS；web→api 不通）。
- 材料目录 GET 经代理失败 → UI 回退种子清单（诚实文案）；**无** demo 别名回潮。
- C4 FAIL 根因口径钉为 **运行态代理/环境**，**非**材料别名回潮；**非**产品口径变更。
- 复测：待运维修 overlay 后可复测 **C4**；在此之前 **C4 挡关**，整关 **未放行**。

## 禁令确认

| 项 | 本记录 |
| --- | --- |
| 建模完成 | **未勾** |
| Maxwell 全功能 / MVP / 重开 v1.0.0 | **未宣称** / **未打 tag** |
| 整机 ≤3% / ≤5% / 外推 F1/F2 | **未勾** / **未外推** |
| Q7-C1…C5 整关 | **不放行**（C4 FAIL 挡关） |
| 产品项 Q7-1…4 / Q7-6 Motor 签字 | **不代关** / **不代签** |
| 业务代码 | **未改** `apps/` |

## 相关链接

- [Q7-冒烟清单](Q7-冒烟清单.md)
- [Q7-验收跟踪](Q7-验收跟踪.md)
- [Q7-冒烟框架说明](Q7-冒烟框架说明.md)
- [Q7-范围冻结](Q7-范围冻结.md) §D
- 截图：[artifacts/q7-c1-c5-browser/](artifacts/q7-c1-c5-browser/)

---

*Mo-测试 · 浏览器目视 · merge tip `0ee6fd3` / FE `7ba2e5e` · 2026-10-29 20:21 Asia/Shanghai · **C4 FAIL 挡关 · 整关未放行** · 根因：代理/Docker DNS · 禁勾建模完成/Maxwell 全功能/MVP/≤3%/≤5%/扩 F1/F2 · 不代关产品/Motor*
