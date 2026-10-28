# Q2-P04 解析 UI 壳冒烟（3be2e67）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:25 Asia/Shanghai |
| 前端 tip | **`3be2e67`** |
| 环境 | `http://127.0.0.1:5173` + API `:8000` |
| 口径 | **UI 壳 only**；local mock；不对标 ≤5%；不调用 /jobs 作权威 |

## 结果

| 项 | 判定 | 证据 |
| --- | --- | --- |
| 登录 | PASS | engineer → `/projects` |
| `/analytic` | PASS | 侧栏「解析」；local-first 文案 |
| PMSM 表+曲线 | PASS | 损耗/电感表；KPI 转矩；T–n 折线可见 |
| BLDC | PASS | mock 表+KPI；转速扫描区在（折线未画出，不挡壳验收） |
| ACIM | PASS | mock 表+KPI（含 rotor_bar）；扫描区在 |

## 结论

**Q2-P04 → 通过（UI 壳）**。真算/jobs 闭环与 ≤5% 对标另议。
