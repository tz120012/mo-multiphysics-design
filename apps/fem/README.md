# apps/fem — Elmer / GetDP 容器（Q3-3）

- **运维**：compose profile `fem`、卷 `mo_femdata`、与 Celery `worker` 共享 `/var/mo/fem`。
- **有限元**：替换本目录 `Dockerfile` 为真实 Elmer/GetDP/Gmsh 工具链；禁止宿主机系统级安装。
- 启动：`make up-worker`（仅 Celery）或 `make up-fem`（worker + fem stub）。
