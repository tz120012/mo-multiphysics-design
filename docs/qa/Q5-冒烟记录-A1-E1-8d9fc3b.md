# Q5 冒烟记录 — A1 mems/files + E1 契约 1.0.0（API @ `8d9fc3b`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 18:29 Asia/Shanghai |
| 业务 tip | **`8d9fc3b`**（`feat(api): Q5-1 mems/files GET + Q5-5 pin 1.0.0 + Q5-2 equationMode honesty`） |
| tip 全 SHA | `8d9fc3bfa5c59ebd141de77f0636f6b543f39e13` |
| 祖先确认 | `git merge-base --is-ancestor 8d9fc3b HEAD` → **0** |
| 实测时 HEAD | **`61f7b53`**（含 `8d9fc3b` / `e3074b9` / `797ce67`） |
| 执行 | Mo-测试；**仅** `docs/qa/` 证据入库；**未**改业务代码；pytest 本侧实跑 |
| 对照 | OpenAPI `docs/drafts/openapi-v1.yaml` version **1.0.0**；`docs/drafts/Q5-1-mems-files边界.md`；`docs/drafts/Q5-5-契约1.0.0钉死.md` |
| 性质 | Motor 交测 Q5-1 / Q5-5；**钉 1.0.0 ≠ MVP**；**禁勾 F1/F2**；**不代签** |

## 环境

| 证据 | 结果 |
| --- | --- |
| 工作目录 | `/workspace/mo-platform` |
| 解释器 | `apps/api/.venv` · Python 3.13.5 · pytest 9.2.0 |
| 入口 | `cd apps/api && source .venv/bin/activate && python -m pytest …` |
| 隔离 | 仅 mo-platform；本轮**未**改 `apps/`/`packages/`；**未** stage 非 `docs/qa` |

## 命令

```bash
cd /workspace/mo-platform/apps/api
source .venv/bin/activate
python -m pytest tests/test_mems_files.py tests/test_fem_equation_mode.py -v --tb=short
# → 12 passed, 2 warnings in ~2.0s
```

本记录关注子集：`tests/test_mems_files.py`（5 项，含 A1 + E1）。

## Q5-A1 — mems/files GET 真实成员 → 200

| # | 用例 | 关键断言（对照测试） | 实测 |
| --- | --- | --- | --- |
| 1 | `test_get_mems_file_member_200` | PUT zip 含 `geometry/params.json` 后 `GET …/mems/files/geometry/params.json` → **200**；`content-type` 以 `application/json` 起；body `{"poleCount":6,"ok":true}`；头 `X-Mo-Mems-Path=geometry/params.json` | **PASSED** |
| 2 | `test_get_mems_file_missing_member_404` | 缺成员 → **404**；`code=mems_member_not_found` | **PASSED** |
| 3 | `test_get_mems_file_path_traversal_400` | `..%2F…` / `%2e%2e` → **400**；`code=bad_path` | **PASSED** |
| 4 | `test_get_mems_file_project_missing_404` | 无工程 → **404** | **PASSED** |

OpenAPI：`GET /projects/{projectId}/mems/files/{path}` 已去 planned，summary 标明 Q5-1。

**A1 结论：PASS（API 成员 GET 可测）**

## Q5-E1 — 契约 1.0.0（读双接受、新写只出）

| # | 证据点 | 关键断言 / 源码 | 实测 |
| --- | --- | --- | --- |
| 1 | `test_mems_schema_dual_accept_draft_and_pin` | 新建工程 meta `memsSchemaVersion == "1.0.0"`；PUT zip 带 `1.0.0-draft` → **200** 且响应 meta **写出 `1.0.0`**；未知 `9.9.9` → **400** | **PASSED** |
| 2 | `apps/api/app/config.py` | `app_version` / `mems_schema_version` 默认 **`1.0.0`** | 已读确认 |
| 3 | `apps/api/app/mems_store.py` | `ACCEPTED_MEMS_SCHEMA_VERSIONS = {"1.0.0","1.0.0-draft"}`；校验双接受；新写走 settings → **只出 1.0.0** | 已读确认 |
| 4 | OpenAPI | 顶层 `version: 1.0.0`；说明「读侧过渡双接受 draft∪1.0.0，新写只出 1.0.0」 | 已读确认 |

**E1 结论：PASS（契约钉 1.0.0；读双接受 / 写只出）**  
> **钉 1.0.0 ≠ 宣称 MVP 已达成**；本项不代签、不打 tag。

## pytest 汇总（本侧）

| 文件 | 结果 |
| --- | --- |
| `tests/test_mems_files.py` | **5 passed** |
| `tests/test_fem_equation_mode.py` | **7 passed**（详见 B1-API 记录） |
| **合计** | **12 passed**（与后端自报一致） |

## 禁令确认

| 项 | 本记录 |
| --- | --- |
| F1 / F2 | **未勾** |
| MVP / tag `v1.0.0` | **未宣称** / **未打** |
| 代签产品「通过」 | **否** |

## 相关链接

- [Q5-冒烟清单](Q5-冒烟清单.md) · [Q5-验收跟踪](Q5-验收跟踪.md)
- [Q5-冒烟记录-B1-API-e3074b9](Q5-冒烟记录-B1-API-e3074b9.md)（同批 pytest）
- CLI 真路径（**未覆盖**）：[Q5-冒烟记录-B1-磁静力学-797ce67](Q5-冒烟记录-B1-磁静力学-797ce67.md)

---

**产品确认（Mo-产品）**：同意 A1/E1 PASS → Q5-1 **通过**、Q5-5 **通过**。证据 tip **`7cdccbc`** @ **`8d9fc3b`**。**钉 1.0.0 ≠ 宣称 MVP**；禁勾 F1/F2；不开 MVP。

---

*Mo-测试 · 交测抽测 · 隔离仅 `/workspace/mo-platform`。*
