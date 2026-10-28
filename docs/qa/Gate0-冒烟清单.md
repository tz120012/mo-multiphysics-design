# Gate0 冒烟清单

> 依据：`docs/02-阶段任务拆解与门禁.md` § Gate0 验收  
> 执行：Mo-测试 · 仓库 tip 以实测时 `git rev-parse --short HEAD` 为准  
> 范围：仅文档存在、骨架目录、CI 空跑占位、compose 服务定义；**不含业务功能**

## 检查项

| ID | 检查项 | 通过标准 | 脚本项 |
| --- | --- | --- | --- |
| G0-S1 | 文档 `01`/`02` 存在 | `docs/01-任务书-v2.md`、`docs/02-阶段任务拆解与门禁.md` 可读 | `check_docs` |
| G0-S2 | 骨架目录 | 存在 `apps/web`、`apps/api`、`packages/solver-analytic`、`scripts`、`docs`，且有 `README.md`、`.gitignore` | `check_skeleton` |
| G0-S3 | git 初始提交 | `git rev-parse HEAD` 成功（非空仓库） | `check_git` |
| G0-S4 | CI 空跑占位 | 存在可触发的 CI 配置（如 `.github/workflows/*.yml`），或等价流水线文件；允许 no-op 成功 | `check_ci` |
| G0-S5 | compose Postgres+Redis | 存在 `docker-compose.yml` / `compose.yml`（或 `docker-compose*.yml`），且文内定义 `postgres`（或 postgresql）与 `redis` 服务 | `check_compose` |
| G0-S6 | 冒烟脚本可执行 | `scripts/smoke_gate0.sh` 可执行并返回明确退出码 | （本清单配套脚本） |

## 流程项（人工 / Motor，脚本不判定）

| ID | 检查项 | 通过标准 |
| --- | --- | --- |
| G0-P1 | 角色确认 | 十角色有人认领或明确代理（见 `02` 角色表） |
| G0-P2 | Motor 签字 | 日期 + 人 + 允许进入 Q1；有遗留项须列明 |

## 执行方式

```bash
cd /workspace/mo-platform
bash scripts/smoke_gate0.sh
```

- 退出码 `0`：G0-S1～S6 全部通过  
- 非 `0`：stdout 列出失败项；**Gate0 不得放行业务代码**

## 实测记录

| 日期 (Asia/Shanghai) | tip | 结果 | 失败项 | 执行人 |
| --- | --- | --- | --- | --- |
| 2026-10-28 11:54 | `29a1cdc`（Motor 指派基线 `703fcb7`；其后有文档/骨架增量，CI/compose 仍缺） | **FAIL** | G0-S4 CI；G0-S5 compose | Mo-测试 |

