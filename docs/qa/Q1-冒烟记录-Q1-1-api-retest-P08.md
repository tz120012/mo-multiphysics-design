# Q1-P08 复测记录（工作树）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 11:59 Asia/Shanghai |
| 仓库 tip | `0b3b7e8`（API 热修在工作区，**尚未整包 commit**） |
| 执行 | Mo-测试 |
| 服务 | 已运行 `127.0.0.1:8000` uvicorn |

## 结果

| 用例 | 期望 | 实测 | 判定 |
| --- | --- | --- | --- |
| GET `/health` | status=ok | status=ok，`version=1.0.0-draft`（db/redis 未起） | PASS |
| GET `/api/v1/projects` 无鉴权 | 401 | 401 | PASS |
| POST 创建 RF/PMSM + Bearer | 201 + schema 1.0.0-draft | 201，`memsSchemaVersion=1.0.0-draft` | PASS |

## 结论

**工作树复测通过 → Q1-P08 跟踪标「通过」**，注明正式关闭以**后端提交 tip 固化**为准。
