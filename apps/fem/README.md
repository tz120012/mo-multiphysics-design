# apps/fem — Elmer / GetDP 容器与 FEM worker（Q3-3）

边界：`docs/drafts/Q3-轴向与FEM边界.md`（tip `8d966d9`）。

| 镜像 | Dockerfile | 角色 |
| --- | --- | --- |
| `fem` | `Dockerfile` | Elmer/GetDP/Gmsh **工具链**（当前 stub；禁宿主机安装） |
| `worker-fem` | `Dockerfile.worker` | Celery **FEM 队列** `fem`；调用/共享 `/var/mo/fem`；**不**进 `apps/api` 进程 |

- Owner：容器与工人镜像 = **Mo-运维**；模板/thinning = **Mo-有限元**（`packages/solver-fem`）
- 启动：`make up-fem` → profiles `worker`（analytic）+ `fem`（toolchain + worker-fem）
- 工作目录：`MO_FEM_WORKDIR=/var/mo/fem`（卷 `mo_femdata`）
