# 本地依赖（Gate0 占位）

```bash
cd /workspace/mo-platform
docker compose up -d
```

- Postgres：`localhost:5433`（用户/库/密码均为 `mo`）
- Redis：`localhost:6380`

Gate0 仅要求 compose **定义存在**；是否真正拉起不阻塞门禁。端口避开常见 5432/6379，降低与其他项目冲突。
