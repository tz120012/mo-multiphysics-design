# Q4+ 冒烟记录 — Q4+-2 compose Web nginx→host 代理

> 执行：Mo-运维 · 交测 tip 以本提交 `git rev-parse --short HEAD` 为准  
> 对照：`docs/02` Q4+-2；清单 [Q4plus-冒烟清单](Q4plus-冒烟清单.md) **Q4+-B1**  
> 时区：Asia/Shanghai

## 1. 现象（复现）

| 步骤 | 命令 / 观察 | 修复前 |
| --- | --- | --- |
| 1 | `make up-box`（或已起的 box 栈）；`.env` 可有 `WEB_HOST_PORT=5174` | web 映射 `0.0.0.0:5174->80` |
| 2 | `curl -m 5 http://127.0.0.1:8000/health` | **200**（api 直连） |
| 3 | `curl -m 5 http://127.0.0.1:5174/` | **200**（静态） |
| 4 | `curl -m 8 http://127.0.0.1:5174/health` | **超时** |
| 5 | `curl -m 8 http://127.0.0.1:5174/api/v1/health` | **超时** |
| 6 | 容器内 `wget http://host.docker.internal:8000/health` | **200**（/etc/hosts 可达） |
| 7 | 容器内 `wget http://api:8000/health` | **bad address**（box mo-net DNS/east-west 不可用，预期） |

## 2. 根因

`apps/web/nginx.box.conf` 使用：

- `resolver 127.0.0.11`（Docker embedded DNS）
- `set $mo_api host.docker.internal:8000; proxy_pass http://$mo_api;`

变量 + resolver **只走 DNS**，**不读** compose `extra_hosts` 写入的 `/etc/hosts`，解析挂起直至代理超时。  
宿主机直连 `:8000` 与容器内 getaddrinfo/`wget` 走 hosts 均正常——故表现为「只有 nginx 反代挂」。

## 3. 修复

- 改为字面量 `proxy_pass http://host.docker.internal:8000`（及 `/health`），去掉 box conf 上的 resolver/变量。  
- 非 box 的 `nginx.conf`（`api:8000` + resolver）不变。  
- 文档：`docs/deploy-local.md`、`docs/deploy-private.md`。

## 4. 复测（本机 box）

| 检查 | 结果 |
| --- | --- |
| `curl -m 5 http://127.0.0.1:5174/` | **200** |
| `curl -m 5 http://127.0.0.1:5174/health` | **200**；`db.ok`/`redis.ok` true；~7 ms |
| `curl -m 5 http://127.0.0.1:5174/api/v1/health` | **200**；同上 |
| 运维结论 | **可测通过**（非「书面不可行」路径） |

复测命令备忘：

```bash
cd /workspace/mo-platform
# 若改过 nginx.box.conf：
docker compose -f docker-compose.yml -f docker-compose.box.yml up -d --force-recreate --no-deps web
curl -sS -m 5 http://127.0.0.1:${WEB_HOST_PORT:-5174}/health
curl -sS -m 5 http://127.0.0.1:${WEB_HOST_PORT:-5174}/api/v1/health
```

## 5. 口径

- **不**宣称 MVP。  
- vite `:5173` 仍可用于 HMR 开发；compose Web 端口以 `.env` `WEB_HOST_PORT` 为准（示例默认 5173）。  
- 请 Mo-测试勾 **Q4+-B1**；Motor 收 tip。
