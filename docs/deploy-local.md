# 本地依赖（Gate0）

前提：Docker Compose v2。

```bash
cp .env.example .env   # 若尚无 .env
make up                # 启动 Postgres 16 + Redis 7
make ps                # 等待 healthy
make smoke             # Gate0 冒烟占位（exit 0）
make down
```

连接约定（容器内）：`DATABASE_URL=postgresql+psycopg://mo:mo@postgres:5432/mo`，`REDIS_URL=redis://redis:6379/0`。宿主机可用 `localhost` 替换主机名。API 对外端口预留 `8000`（Gate0 未启 api 服务）。
