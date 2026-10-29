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

## Q5-2 磁静力学真路径

- 边界：`docs/drafts/Q5-2-真磁静力学后处理.md`（+ Q4plus-5 分界）
- 模板：`templates/af_pmsm_3d_ms/`（WhitneyAV + Maxwell；`magnetostaticPathReady=true`；`pending_calibration`）
- 真路径冒烟：`python3 packages/solver-fem/smoke/run_magnetostatic_truepath.py`
- 旧壳：`python3 packages/solver-fem/smoke/run_magnetostatic_shell.py`
- heat-proxy（`rf_pmsm_2d` / `af_pmsm_3d`）**保留不动**
- **禁宣称** FEM ≤3% / MVP（Q5-4 才出标定报告）

## Q7-3 同壳后处理（协作）

- 边界：`docs/drafts/Q7-3-同壳后处理-FEM协作.md`（开闸 `30a37a7`；**零新 API**）
- 主路径：UEM `lastFemJobId` / `resultRef` → 既有 `GET /jobs/{id}/artifacts`
- 契约 smoke：`python3 packages/solver-fem/smoke/run_q7_shell_postprocess_contract.py`（无 Elmer）
- **不改** thinning / Elmer 核心；heat-proxy ≠ MS；禁勾精度

