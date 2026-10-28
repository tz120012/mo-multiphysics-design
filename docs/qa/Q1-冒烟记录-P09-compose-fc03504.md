# Q1-P09 compose 冒烟记录（复测 tip `fc03504`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:18 Asia/Shanghai |
| 仓库 tip | **`fc03504`** `ops(P09): add make up-box overlay for Bot iptables-stub smoke`（`git merge-base --is-ancestor fc03504 HEAD` 成立；复测时 HEAD=`f10aaee`） |
| 执行 | Mo-测试执行员（独立复测，不采信口头绿） |
| 命令 | 本机无 `make`；等价：`docker compose --env-file .env down` → `docker compose -f docker-compose.yml -f docker-compose.box.yml --env-file .env up -d --build` → health-box 等价 curl/`ps`（均 `sudo -n docker`） |
| 端口 | Postgres **5433** / Redis **6380** / API **8000** / Web **5174**（`.env` 中 `WEB_HOST_PORT=5174`，例文件默认 5173） |

前次阻塞见 [Q1-冒烟记录-P09-compose-4538501.md](Q1-冒烟记录-P09-compose-4538501.md)（tip `4538501`：四服务 healthy 但 `db.ok`/`redis.ok`=false，容器 DNS）。

## 前置抽查

| 项 | 结果 |
| --- | --- |
| `fc03504` 在祖先链 | **YES** |
| `docker-compose.box.yml` | 有：api/web `extra_hosts` host-gateway；api `DATABASE_URL`/`REDIS_URL` → `host.docker.internal:5433/6380`；web 挂载 `nginx.box.conf` |
| Makefile `up-box`/`health-box`/`down-box` | 有（本机无 make，按等价 compose 执行） |
| `.env` | 已存在（未覆盖）；`API_HOST_PORT=8000` |

## `compose ps`（box overlay）

| 服务 | STATUS | 端口 |
| --- | --- | --- |
| mo-postgres | Up (**healthy**) | 0.0.0.0:**5433**→5432 |
| mo-redis | Up (**healthy**) | 0.0.0.0:**6380**→6379 |
| mo-api | Up (**healthy**) | 0.0.0.0:**8000**→8000 |
| mo-web | Up (**healthy**) | 0.0.0.0:**5174**→80 |

api 容器环境实测：`DATABASE_URL=...@host.docker.internal:5433/mo`，`REDIS_URL=redis://host.docker.internal:6380/0`。

## `GET http://127.0.0.1:8000/health`（原文）

```json
{
    "status": "ok",
    "version": "1.0.0-draft",
    "time": "2026-10-28T04:18:03.064105+00:00",
    "db": {
        "ok": true
    },
    "redis": {
        "ok": true
    }
}
```

| 口径 | 期望 | 实测 | 判定 |
| --- | --- | --- | --- |
| 四服务 healthy | 全 healthy | postgres/redis/api/web 均 healthy | **PASS** |
| `status` | `ok` | `ok` | **PASS** |
| `db.ok` | `true` | **true** | **PASS** |
| `redis.ok` | `true` | **true** | **PASS** |

## Web 附加抽查（非硬关闸项）

| 检查 | 实测 | 说明 |
| --- | --- | --- |
| `GET :5174/` | **200** HTML，`Server: nginx/1.27.5` | 静态 PASS |
| `GET :5174/health` / `/api/...` | curl **timeout**；nginx error：`recv() failed (111) while resolving, resolver: 127.0.0.11:53` | web→`host.docker.internal` 仍受容器 DNS/iptables-stub 影响；**不纳入本轮 P09 硬口径**（硬口径为四服务 healthy + `:8000/health` db/redis ok） |

## 结论

- **四服务 healthy 且 `GET :8000/health` → `status=ok`、`db.ok=true`、`redis.ok=true`：达成。**
- **Q1-P09 → 通过**（box 兜底 tip `fc03504` 独立复测）。
- 观察：`.env` Web 宿主机口为 **5174**（非例文件 5173）；nginx box 反代因容器 DNS 仍超时——记录备查，不挡本轮关闭。
- **未改动** P04/开项③、P05–P07、开项① 等已通过项。
