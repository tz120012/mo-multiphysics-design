# apps/fem — Elmer / Gmsh 容器（Q3-L2）

| 项 | 说明 |
| --- | --- |
| 镜像体 | 本目录 `Dockerfile`（Ubuntu 22.04 + Elmer CSC PPA + gmsh） |
| Compose | Mo-运维：`profile fem` / `make up-fem`；卷 `mo_femdata` → `/var/mo/fem` |
| Worker | `Dockerfile.worker` 跑 Celery `-Q fem`；求解二进制在本镜像，可由 `docker compose exec fem` 调用 |
| 宿主机 | **禁止**安装 Elmer / GetDP / Gmsh |

## 本地构建（box）

```bash
# 须在仓库根；compose 同路径
docker build -f apps/fem/Dockerfile -t mo-fem:q3-l2 .
docker run --rm mo-fem:q3-l2 ElmerSolver
```

GetDP：F2 Elmer-first；若 apt 无包则镜像内可缺，不阻塞 Q3。

## 与 solver-fem

模板与 dry-run：`packages/solver-fem/`。`MO_FEM_DRY_RUN=0` 且本镜像就绪后，工人可改调真实 Elmer。
