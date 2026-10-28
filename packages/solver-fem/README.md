# packages/solver-fem

| 项 | 值 |
| --- | --- |
| 状态 | **Q3 授权立包**（Gate0「不立」已解除；见 `docs/drafts/Q3-轴向与FEM边界.md`） |
| Owner | **Mo-有限元**（模板 / thinning / schema）；容器与工人镜像归 **Mo-运维** |
| 内核 | Elmer / GetDP（**禁止**本包或 box 宿主机系统级安装；Gmsh 仅容器内） |

## 本包包含

- 前处理 / 网格 / 求解 **模板**（`templates/`）
- Job payload、manifest、result index 的 JSON Schema（`api/`）
- 结果精简（thinning）约定的落地辅助（由 Mo-有限元实现）

## 本包不包含

- Elmer / GetDP / Gmsh 二进制
- FastAPI 路由（Jobs 在 `apps/api`；FEM **只**经 `jobType=fem`）

## Q3 顺序

- 径向 2D：PMSM → ACIM → BLDC
- 轴向 3D：AF PMSM 最小路径

## `.mems` 写出

```text
solver/fem/jobs/{jobId}/manifest.json
results/fem/{jobId}/          # JSON scalars + glTF/GLB + PNG
```

细则：`docs/drafts/Q3-轴向与FEM边界.md`。
