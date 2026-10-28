# 本地一键开发环境（Q1-8 / P09）

**维护：Mo-运维。** 仅 `/workspace/mo-platform`。  
目标：一次 `make up` 拉起 **web + api + Postgres + Redis**，health / db / redis 变绿。

## 前提

- Docker Compose **v2**
- 端口空闲：**5433**（Postgres）、**6380**（Redis）、**8000**（API）、**5173**（Web）

## 步骤

```bash
cd /workspace/mo-platform
cp .env.example .env    # 首次
make up                 # build + 后台启动四服务
make ps                 # 四服务 healthy
make health             # curl /health，检查 db.ok / redis.ok
```

等价：`./scripts/start-deps.sh`

停下：`make down`。看日志：`make logs`。

## 验收标准（P09）

| 检查 | 期望 |
| --- | --- |
| `docker compose ps` | `postgres` / `redis` / `api` / `web` 均为 healthy（或 running+health 通过） |
| `GET http://127.0.0.1:8000/health` | `status=ok`，`db.ok=true`，`redis.ok=true` |
| Web | 浏览器打开 http://127.0.0.1:5173 ，`/api/v1` 经 nginx 反代到 api |

## 端口与连接

| 用途 | 地址 |
| --- | --- |
| 宿主机 Postgres | `localhost:5433` → 容器 `5432` |
| 宿主机 Redis | `localhost:6380` → 容器 `6379` |
| 宿主机 API | `localhost:8000` |
| 宿主机 Web | `localhost:5173` |
| 容器内（api） | `postgres:5432` / `redis:6379` |

`.env.example` 约定（与 Mo-后端一致，勿改变量名）：

- `DATABASE_URL=postgresql+psycopg://mo:mo@postgres:5432/mo`
- `REDIS_URL=redis://redis:6379/0`
- 用户 / 密码 / 库：`mo` / `mo` / `mo`

宿主机直连（API 跑在宿主机、不进 compose 时）：

- `postgresql+psycopg://mo:mo@127.0.0.1:5433/mo`
- `redis://127.0.0.1:6380/0`

## 镜像与构建

| 服务 | 上下文 |
| --- | --- |
| `api` | 仓库根上下文 + `apps/api/Dockerfile`（打入 `packages/solver-analytic`，uvicorn :8000） |
| `web` | `apps/web/Dockerfile`（pnpm build + nginx，反代 `/api/` → `api:8000`） |
| `postgres` | `postgres:16-alpine` |
| `redis` | `redis:7-alpine` |
| `worker`（可选 profile） | 同 api 镜像；`celery -A app.celery_app worker` |
| `fem`（可选 profile） | `apps/fem/Dockerfile`（Q3-3 Elmer/GetDP stub，禁宿主机安装） |

## CI / 冒烟

- `.github/workflows/ci.yml` → `scripts/smoke.sh`（占位 exit 0）
- 本地：`make smoke`

## 故障排查

1. 端口占用：改 `.env` 里 `POSTGRES_PORT` / `REDIS_PORT` / `API_HOST_PORT` / `WEB_HOST_PORT`（**不要**把默认宿主机映射改回 5432/6379）。
2. `db.ok=false`：等 postgres healthy 后 `docker compose restart api`。
3. 重建：`make down && make up`。


## 本机验收记录（Mo-运维）

在具备正常 Docker 网络（iptables/bridge）的机器上执行：

```bash
make up && make health
# 期望：db.ok=true redis.ok=true；web http://127.0.0.1:5173
```

若宿主机 **8000/5173** 已被占用，可在 `.env` 临时改 `API_HOST_PORT` / `WEB_HOST_PORT`（**不要**改回 Postgres/Redis 宿主机 5432/6379）。

依赖健康（不经容器 DNS）也可用：

```bash
# 容器已 publish 时
python -c "..."  # 或 make health 指向 API
# Postgres: localhost:5433  Redis: localhost:6380
```


## Bot / box 冒烟兜底（`make up-box`）

**仅当**默认 `make up` 后四服务 healthy，但 `GET /health` 里 `db.ok`/`redis.ok` 为 false（容器内解析不了 `postgres`/`redis`，常见于缺真实 iptables 的 Bot 电脑）。

**不要**把这套当成正常开发默认路径。

```bash
cd /workspace/mo-platform
make down          # 先停掉默认栈（如已起）
make up-box        # 使用 docker-compose.yml + docker-compose.box.yml
make health-box    # 期望 db.ok=true redis.ok=true
```

原理：`docker-compose.box.yml` 让 **api** 通过 `host.docker.internal`（`extra_hosts: host-gateway`）访问宿主机已 publish 的 **5433/6380**；**web** 挂载 `apps/web/nginx.box.conf`，把 `/api` 反代到 `host.docker.internal:8000`。

正常 Docker 主机请继续：

```bash
make up && make health
```


## Q3-3 Celery 工人与 FEM 容器

边界锁定：[Q3-轴向与FEM边界.md](./drafts/Q3-轴向与FEM边界.md)（tip `8d966d9`）。  
**禁止** box 宿主机安装 Elmer/GetDP/Gmsh；**禁止** Elmer 进入 `apps/api` uvicorn 进程。

默认 `make up` / `make up-box` **仍是四服务**（web/api/postgres/redis）。

| 目标 | 命令 | 说明 |
| --- | --- | --- |
| 仅 analytic Celery | `make up-worker` | profile `worker`（api 镜像）；`CELERY_ENABLED=1` |
| FEM 栈 | `make up-fem` | profiles `worker` + `fem`：`fem` 工具链 stub + `worker-fem`（队列 `fem`） |

| 服务 | 镜像 | 说明 |
| --- | --- | --- |
| `worker` | api 镜像 | analytic 队列（Q2-6） |
| `fem` | `apps/fem/Dockerfile` | Elmer(+Gmsh) 工具链；GetDP 可后置 stub |
| `worker-fem` | `apps/fem/Dockerfile.worker` | Celery `-Q fem`；共享 `/var/mo/fem` |

- 工作目录：`MO_FEM_WORKDIR=/var/mo/fem`（卷 `mo_femdata`）
- 模板/schema：`packages/solver-fem`（Mo-有限元）；Jobs `jobType=fem`（Mo-后端入队）

### Q2-L7 抽检（开 Q3 前）

```bash
make up-box && make health-box
# 期望四服务 healthy；GET :8000/health → status=ok, db.ok=true, redis.ok=true
```
