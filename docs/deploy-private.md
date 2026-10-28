# 私有化部署手册（草稿）

> **状态：草稿** — 待 Motor / 评审确认后再升正式版。  
> **维护：Mo-运维。** 仅 `/workspace/mo-platform`。  
> 源材料：[deploy-local.md](./deploy-local.md)；任务备案：[drafts/Q4-10-压测与私有化.md](./drafts/Q4-10-压测与私有化.md)。

## 目的

在 **on-prem / 近气隙（air-gapped-ish）** 环境下，用 Docker Compose 拉起 Mo 栈，**不依赖公有云 SaaS**（无托管 DB、云 Redis、外部鉴权 SaaS 等非必需）。  
本手册描述「干净机 → 四服务健康 →（可选）worker / FEM dry-run」的可复现路径；压测入口见 `make stress`（`scripts/stress-smoke.sh`）与 Jobs 扩展 `make stress-jobs`（`scripts/stress-jobs.sh`，analytic/fem dry-run）。

## 主机要求

| 项 | 要求 |
| --- | --- |
| 运行时 | Docker + **Compose v2**（`docker compose`） |
| 磁盘 | 至少留足镜像层 + 卷：Postgres/Redis 数据、可选 `mo_femdata`；建议预留数 GB 以上（FEM 镜像含 Elmer/Gmsh 时更大） |
| 网络 | 内网即可；首次需能拉取/导入基础镜像（`postgres:16-alpine`、`redis:7-alpine`）及本地 build |
| **禁止** | **禁止在宿主机安装 Elmer / GetDP / Gmsh**；FEM 仅容器内（profile `fem` / `worker-fem`） |

正常 Docker 主机用 `make up`；Bot/box 缺真实 iptables 时用 `make up-box` / `make up-fem-box`（见 [deploy-local.md](./deploy-local.md)「Bot / box 冒烟兜底」）。

## 端口表

宿主机默认映射（**切勿**改回宿主机默认 `5432` / `6379`，以免与其它项目冲突）：

| 用途 | 宿主机 | 容器内 |
| --- | --- | --- |
| Postgres | **5433** | `5432` |
| Redis | **6380** | `6379` |
| API | **8000** | `8000` |
| Web | **5173** | `80`（nginx） |

容器内服务 DNS：`postgres:5432` / `redis:6379`（api / worker 用）。

## 镜像与卷清单

摘自 `docker-compose.yml`：

| 服务 | 镜像 / 构建 | 默认 | 卷 |
| --- | --- | --- | --- |
| `postgres` | `postgres:16-alpine` | 是 | `mo_pgdata` → `/var/lib/postgresql/data` |
| `redis` | `redis:7-alpine` | 是 | `mo_redisdata` → `/data` |
| `api` | 根上下文 + `apps/api/Dockerfile` | 是 | — |
| `web` | `apps/web/Dockerfile`（pnpm build + nginx） | 是 | —（box overlay 可挂 `nginx.box.conf`） |
| `worker` | 同 api 镜像；profile **`worker`** | 可选 | `mo_femdata` → `/var/mo/fem` |
| `fem` | `apps/fem/Dockerfile`；profile **`fem`** | 可选 | `mo_femdata` |
| `worker-fem` | `apps/fem/Dockerfile.worker`；profile **`fem`** | 可选 | `mo_femdata` |

网络：`mo-net`。

## 步骤

```bash
cd /workspace/mo-platform   # 或私有化机上的仓库根
cp .env.example .env        # 首次；按需改口令，保留端口约定
make up                     # 默认四服务（正常 Docker DNS）
# 或：make up-box           # Bot/box 冒烟（host.docker.internal）
# 或：make up-fem-box       # box + worker + fem（默认 MO_FEM_DRY_RUN=1）

make ps                     # 期望 postgres/redis/api/web healthy
make health                 # 或 make health-box
# 期望 GET :8000/health → status=ok，db.ok=true，redis.ok=true
```

等价依赖启动：`./scripts/start-deps.sh`（见本地文档）。

轻量压测骨架（栈已起、仅 curl）：

```bash
make stress                 # BASE_URL / CONCURRENCY / REQUESTS 可环境变量覆盖
make stress-jobs            # JOBS_N / POLL_SEC；analytic + fem dry-run 入队轮询
```

## 配置面（关键 `.env`）

与 `.env.example` / Mo-后端约定一致（**勿擅自改名**）：

| 变量 | 作用 |
| --- | --- |
| `DATABASE_URL` | 容器内 Postgres（默认 `postgresql+psycopg://mo:mo@postgres:5432/mo`） |
| `REDIS_URL` | 容器内 Redis（默认 `redis://redis:6379/0`） |
| `CELERY_ENABLED` | `0` 默认；`make up-worker` / `up-fem*` 时置 `1` |
| `MO_FEM_DRY_RUN` | **默认 `1`（stub）**；真 Elmer 仅临时命令行覆盖，见下 |
| `SOLVER_ANALYTIC_PATH` / `SOLVER_FEM_PATH` | 镜像内 solver 包路径 |
| `WEB_HOST_PORT` | Web 宿主机口（示例默认 **5173**；亦可 5174，见 Q4+-2） |
| `POSTGRES_PORT` / `REDIS_PORT` / `API_HOST_PORT` | 宿主机映射，默认 5433 / 6380 / 8000 |

宿主机直连 DB/Redis（API 不进 compose 时）：`127.0.0.1:5433` / `127.0.0.1:6380`。

## Profiles

| Profile | 命令 | 说明 |
| --- | --- | --- |
| （默认） | `make up` / `make up-box` | **四服务**：postgres、redis、api、web |
| `worker` | `make up-worker` | + analytic/drive + **optimize** 队列（`-Q celery,optimize`） |
| `worker` + `fem` | `make up-fem` / `make up-fem-box` | + FEM 工具链 sidecar + `worker-fem`（队列 `fem`） |

## 回滚

```bash
make down          # 含 worker/fem profiles 一并停
# 或
make down-box
```

- `down` **默认不删命名卷**；Postgres/Redis/FEM 数据仍在 `mo_pgdata` / `mo_redisdata` / `mo_femdata`。  
- 需彻底清空数据时再显式 `docker volume rm`（**生产前务必确认备份**；本草稿不展开）。

## Web 反代（Q4+-2）

- box overlay：`apps/web/nginx.box.conf` 用字面量 `proxy_pass http://host.docker.internal:8000`（依赖 `extra_hosts` → `/etc/hosts`）。  
- **勿**在 box conf 使用 `resolver 127.0.0.11` + 变量 `proxy_pass` 指 `host.docker.internal`（Docker DNS 看不到 extra_hosts，会超时）。  
- 默认 nginx（非 box）仍反代服务名 `api:8000`。  
- 私有化验收：API `:8000/health` + compose Web（`WEB_HOST_PORT`，示例 5173）`/health` / `/api/...`；vite `:5173` 仍可用作开发冒烟。

## FEM

- 默认 **`MO_FEM_DRY_RUN=1`**（compose / `.env.example`）；**不要**在运行中随意翻成 0。  
- 真 Elmer 端到端临时开关、rebuild、测完改回：见 [deploy-local.md](./deploy-local.md) **「Q3-L2 真 Elmer 联调」**。  
- **勿宣称** FEM 精度（≤3% / ≤5% 等）。

## 相关文档

- [deploy-local.md](./deploy-local.md) — 本地一键与 box / FEM 细节  
- [drafts/Q4-10-压测与私有化.md](./drafts/Q4-10-压测与私有化.md) — Q4-10 范围与验收  
- `scripts/stress-smoke.sh` — 压测入口骨架（`make stress`）
- `scripts/stress-jobs.sh` — Jobs analytic/fem dry-run 入队扩展（`make stress-jobs`）
- [qa/Q4-10-压测与私有化演练.md](./qa/Q4-10-压测与私有化演练.md) — 压测跑数与演练报告（进行中）
