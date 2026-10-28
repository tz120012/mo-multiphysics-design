# Q1-1 API 冒烟记录

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 11:58 Asia/Shanghai |
| 基线 | `d2654f3`（实测仓库 tip 其后；API 进程已在 127.0.0.1:8000） |
| 执行 | Mo-测试 |

## 结果

| 用例 | 期望 | 实测 | 判定 |
| --- | --- | --- | --- |
| GET `/health` | `status=ok`（db 可 false） | `status=ok`, db/redis `ok=false`（5433/6380 未起） | PASS |
| GET `/api/v1/projects` 无鉴权 | 401 | 401 + Missing or invalid Authorization | PASS |
| POST `/api/v1/projects` + Bearer demo | 201，工程可列出 | 201，`RF`/`PMSM`，列表 total≥1 | PASS |
| memsSchemaVersion 默认 | `1.0.0-draft` | **`0.1.0-draft`**（config 默认） | **FAIL（已知，后端待修）** |
| OpenAPI | 含 health/projects | `/openapi.json` 路径齐全，app version 0.1.0 | PASS（路径） |

## 结论

Q1-1 **功能冒烟通过**；**schema 版本未对齐 1.0.0-draft**，跟踪表 Q1-P08 保持「待测」直至后端修正后复测。
