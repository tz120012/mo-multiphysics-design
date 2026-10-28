# Q4 冒烟记录 — 前端 tip `7a45369`（Q4-P05 /compare）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:41 Asia/Shanghai |
| 指派 tip | **`7a45369`**（`feat(web): Q4-5 /compare drive-mode side-by-side (samples)`） |
| 叠样例 tip | **`11e7027`**（`feat(drive): add ACIM V/f and induction FOC public samples for /compare`） |
| 仓库 HEAD（入库时） | 见本证据 commit；`7a45369` / `11e7027` 均为祖先 |
| 执行 | Mo-测试（**浏览器 computerUse 实测结论照抄入库**；**未**重跑 UI） |
| 入口 | URL `http://127.0.0.1:5173/compare`；会话 **demo**；**未**点 drive/solve |
| 范围 | Q4-P05 同屏对比（fixture MVP）；**不**要求 `/drive/solve×2`；**不**宣称解析 ≤5% / FEM ≤3%；**不开宣称 MVP**；**不开 P11** |

## 环境

| 证据 | 结果 |
| --- | --- |
| 祖先 | `git merge-base --is-ancestor 7a45369 HEAD` → 0；`11e7027` → 0 |
| UI BASE_URL | **`http://127.0.0.1:5173`**（vite；规避 compose `:5174`） |
| 鉴权 | 会话 **demo** |
| 未做 | **未**点 drive/solve；**未**重跑本轮 UI（照抄主会话 computerUse 结果） |
| 未改 | **未**改 `apps/` / `packages/` 业务代码；本记录仅 `docs/qa/` |

## 浏览器实测（照抄入库；勿重跑）

| # | 检查项 | 结果 | 备注 |
| --- | --- | --- | --- |
| 1 | 页面/导航「对比」 | **PASS** | `/compare` 可达 |
| 2 | 四样例 | **PASS** | 永磁：A `bldc_square` + B `pmsm_foc`；ACIM：A `acim_vf` + B `acim_foc`（**按族成对**，非四独立下拉） |
| 3 | 永磁 \| ACIM 切换 | **PASS** | 族切换可用 |
| 4 | 转矩 overlay + lossesW | **PASS** | 折线 `torque_nm` vs `t_s`；柱状 copper/iron/… |
| 5 | A/B/Δ 表 | **PASS** | 对比表可见 |
| 6 | 导出 JSON/CSV | **PASS** | Downloads：`drive-compare-acim.json` / `drive-compare-acim-metrics.csv` |

### 缺口（不否决）

- 页脚禁宣称 ≤3%/≤5%（本轮**未**勾选达标）。
- ACIM `magnetEddy` 为「—」。
- 样例按族成对（非四独立下拉）；fixture MVP，**不**要求 solve×2。

### 截图（可选；未强制复制进仓库）

- 主会话 store assets：永磁 / ACIM 对比 png（完整 path 在主会话；本记录不强制 `git add`）。
- 例：`/cursor/stores/.../agents/.../assets/*.png`（哈希文件名；可选备查）。

## 未做 / 禁止宣称

- **未**勾选或宣称解析相对标杆 **≤5%** / FEM **≤3%**。
- **未**宣称 MVP；**未**开 Q4-P11（维持 **未开始**）。
- **未**要求或实测 `/drive/solve×2`（fixture MVP 口径）。
- **未**改 `packages/` / `apps/`；**未**把他人 WIP 打进本 commit。

## 跟踪 / 清单变更

| 项 | 变更 |
| --- | --- |
| Q4-P05 | **待测 → 通过（UI fixture /compare）**；备注 fixture MVP、不要求 solve×2；证据本记录 @ **`7a45369`** 叠 **`11e7027`** |
| P01–P04 / P06–P10 | **保持已通过**（本轮不冲） |
| P08 | **保持通过（CLI shell / pending_calibration）** |
| P11 | **维持未开始**（本轮**不开**） |
| 清单 Q4-C1 | **SKIP → PASS**（UI fixture /compare @ `7a45369`） |
| 清单 Q4-G1 / G2 | **禁止勾选**（未宣称 ≤5%/≤3%） |

## 结论

| 项 | 结论 |
| --- | --- |
| tip `7a45369` `/compare` UI fixture | **PASS**（6/6 项；照抄 computerUse；未重跑） |
| 对标 ≤5% / ≤3% | **未宣称**（禁止） |
| MVP | **未宣称** |
| 产品项 P05 | **通过（UI fixture /compare）** |
| P11 | **未开始**（不开） |
