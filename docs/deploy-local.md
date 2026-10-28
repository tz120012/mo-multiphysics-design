# 本地依赖启动（Mo-运维维护）

前提：Docker Compose v2。仅操作 `/workspace/mo-platform`。

## 一键起依赖

```bash
cd /workspace/mo-platform
cp .env.example .env   # 若尚无 .env
make up                # Postgres 16 + Redis 7
make ps                # 等待 healthy
make smoke             # Gate0/CI 冒烟脚本（exit 0）
make down
```

等价：`./scripts/start-deps.sh`（若存在）或 `docker compose --env-file .env up -d`。

## 端口与连接

| 用途 | 地址 |
| --- | --- |
| 宿主机 Postgres | `localhost:5433` → 容器 `5432` |
| 宿主机 Redis | `localhost:6380` → 容器 `6379` |
| 容器内（后端服务） | `postgres:5432` / `redis:6379` |

环境变量（见 `.env.example`，与 Mo-后端约定一致）：

- `DATABASE_URL=postgresql+psycopg://mo:mo@postgres:5432/mo`
- `REDIS_URL=redis://redis:6379/0`
- 用户 / 密码 / 库：`mo` / `mo` / `mo`

宿主机直连示例：`postgresql+psycopg://mo:mo@localhost:5433/mo`，`redis://localhost:6380/0`。

API 对外端口预留 `8000`（当前 compose 未启 api）。

## CI

- 工作流：`.github/workflows/ci.yml`（push / PR / `workflow_dispatch`）
- 本地等价：`make smoke` → `bash scripts/smoke.sh`
- 清单占位：`docs/smoke-gate0.md`

Q1 起：后端需要依赖时跑 `make up`；真跑 CI / 观测由 Mo-运维继续补强。
