# Q3 FEM 开工包（Mo-有限元）

> 配套：`Q3-轴向与FEM边界.md`、`packages/solver-fem`、`apps/fem`、`make up-fem`  
> 误差：FEM ≤3% **待校准**，不得口头宣称达标。

## 已落地

| 项 | 路径 / 说明 |
| --- | --- |
| Q3-3 dry-run 入队 | `app.tasks.fem.run_fem_job`；`POST /jobs` `jobType=fem` |
| Q3-4 模板 | `packages/solver-fem/templates/rf_pmsm_2d/` |
| Q3-5 模板 | `packages/solver-fem/templates/af_pmsm_3d/` |
| 精简产物 | `thinning.py` → manifest + scalars JSON + glTF + PNG |
| 前端 fixture | `packages/solver-fem/fixtures/rf_pmsm_2d_dryrun/` |
| 容器 Q3-L2 | `apps/fem/Dockerfile`：Ubuntu22.04 + `elmerfem-csc` + `gmsh`（PPA） |

## 冒烟

```bash
cd packages/solver-fem && python3 -m unittest tests.test_dry_run -v
# API in-process（无需 Elmer）:
# POST /api/v1/jobs {"jobType":"fem","projectId":"...","payload":{...}} → poll succeeded
make up-fem   # worker + fem stub；默认 make up 不拉 FEM
```

## 与运维对齐

- Dockerfile 真工具链替换 `apps/fem/Dockerfile` 体；宿主机禁止装 Elmer/GetDP/Gmsh
- 卷：`mo_femdata` → `/var/mo/fem`
- env：`SOLVER_FEM_PATH`、`MO_FEM_WORKDIR`、`MO_FEM_DRY_RUN`

## Motor 拍板对齐（tip `27a8de2` §8）

- **F1**：精简件进 mems-zip + `resultRef`；全场默认不进浏览器，超顶留 worker 盘 → 书面 [Q3-F1-结果精简.md](./Q3-F1-结果精简.md)
- **F2**：**Elmer-first**；GetDP = 枚举 + 模板 stub，双核同验不阻塞 Q3

## 未决

- heat-proxy E2E 已通（`MO_FEM_DRY_RUN=0`，tip `2c1fed6`）；**保留** HeatEquation 模板
- 磁静力学真值路径（骨架 + 冒烟壳）：见 [Q4plus-5-磁静力学与轴向真值.md](./Q4plus-5-磁静力学与轴向真值.md)；真 Elmer MS + Maxwell 后处理仍后置；`pending_calibration`
- GetDP 真跑通（非 Q3 硬阻塞）

## Q3-L2 Dockerfile

已替换 stub 为真工具链安装（仍须 `docker build` / `make up-fem` 重建验证）。宿主机无 Elmer。

## 下一步（Q4）

- [Q4-7-热闭环-FEM损耗输入.md](./Q4-7-热闭环-FEM损耗输入.md)：电磁损耗输入契约（LPTN 主责解析；驱动分损耗）
- [Q4-8-轴向磁拉力.md](./Q4-8-轴向磁拉力.md)：AF 轴向磁拉力 / 变形 / 轴承载荷专项（占位标量仍有效）
- [Q4plus-5-磁静力学与轴向真值.md](./Q4plus-5-磁静力学与轴向真值.md)：磁静力学 ≠ heat-proxy；真值路径壳 `run_magnetostatic_shell.py`
