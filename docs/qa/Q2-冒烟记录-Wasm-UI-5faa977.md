# Q2 冒烟记录 — Wasm UI tip `5faa977`

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:33 Asia/Shanghai |
| 前端 tip | **`5faa977`**（`feat(web): wire solver-analytic-wasm loader with soft-fail`） |
| 祖先确认 | `git merge-base --is-ancestor 5faa977 HEAD` → **0（是祖先）** |
| 仓库 HEAD（写证据时） | 以提交本记录时 `git rev-parse --short HEAD` 为准 |
| 执行 | Mo-测试执行员（人工/浏览器实测，Motor 指派） |
| URL | **`http://127.0.0.1:5173/analytic`**（**勿用** `:5174`） |
| 口径 | Wasm UI 冒烟；路径 pill=`wasm`；**不对标 ≤5%**；空白扫描图不否决 |

## 步骤摘要

1. 打开 `http://127.0.0.1:5173/analytic`（确认 tip `5faa977` 在祖先链）。
2. 分别切换 **PMSM / BLDC / ACIM**，各点一次求解。
3. 核对路径 pill：须为 **wasm**（文案「路径：Wasm」/ `path=wasm`，`mock=false`）；**不得**出现 sync/fixture 回退。
4. 核对 KPI / 损耗表 /（PMSM）T–n；扫描图空白不否决。
5. **不对标 ≤5%**（本轮不宣称误差达标）。

## 三机型结果

| 机型 | 路径 pill | solver | KPI | 损耗/结果表 | 扫描/T–n | 判定 |
| --- | --- | --- | --- | --- | --- | --- |
| PMSM | **wasm**（`mock=false`；无 sync/fixture 回退） | `mec` | 有 | 有 | T–n 有 | **PASS** |
| BLDC | **wasm**（`mock=false`；无 sync/fixture 回退） | `mec` | 有 | 有 | 转速扫描几乎空白（不否决） | **PASS** |
| ACIM | **wasm**（`mock=false`；无 sync/fixture 回退） | `acim_equiv` | 有 | 有 | 扫描几乎空白（不否决） | **PASS** |

## 不对标声明

- 本轮 **不对标 ≤5%**；不得据此宣称相对标杆误差达标。
- 空白扫描图 **不否决**（pill=`wasm` 且 KPI/表已展示即可）。

## 未动项

- **未**改 Q2-P01 / Q2-P05 / Q2-P06 / Q2-P07 无关行状态（仅升 P02/P03/P04 闭环口径）。
- **未**改业务代码；仅 `docs/qa`。

## 结论

| 项 | 结论 |
| --- | --- |
| tip `5faa977` 祖先 | **确认** |
| 三机型 pill=`wasm` + KPI/表 | **PASS** |
| 阻塞 | **无** |
| 总评 | **PASS** |
| 跟踪表建议 | P02/P03/P04 → **通过（Wasm UI 闭环）**；**不对标 ≤5%** |
