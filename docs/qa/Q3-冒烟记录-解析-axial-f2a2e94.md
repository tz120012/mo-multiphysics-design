# Q3 冒烟记录 — 解析 tip `f2a2e94`（Q3-1 / P01 解析侧）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:45 Asia/Shanghai |
| 指派 tip | **`f2a2e94`**（`feat(solver): AF PMSM axial multi-plane unfold + smoke`） |
| 仓库 HEAD（实测时） | `7db0706`（`f2a2e94` 为 HEAD 祖先） |
| 执行 | Mo-测试执行员 |
| 入口 | **CLI / `solve.py`**（`packages/solver-analytic/smoke/run_axial_pmsm_planes.py`）；**非** compose API（见下） |
| 范围 | 仅 AF+PMSM 轴向多平面解析主口径 + RF mec/mock/acim 回归抽测；**不**宣称解析 ≤5% / FEM ≤3% |

## 环境

- `git merge-base --is-ancestor f2a2e94 HEAD` → exit 0。
- 主路径：`python3 packages/solver-analytic/smoke/run_axial_pmsm_planes.py`（fixture 默认路径）。
- RF 回归：同目录 `run_radial_pmsm_mec.py` / `run_radial_pmsm_mock.py` / `run_radial_acim_equiv.py`。
- compose `mo-api` 当时 Up(healthy)，但镜像内 `axial_planes/` 仅 README、无 fixture；`POST …/solver/analytic/solve?solver=mec` + AF fixture → **HTTP 400** `not_implemented`（Axial Q3 未打入该镜像）。本项按 Motor 允许改用 **CLI/solve**；**不**以 compose 400 判本 tip 失败。
- 未改 `apps/` 业务代码；本记录仅文档。

## Motor 硬口径

| # | 硬口径 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | tip `f2a2e94` 是 HEAD 祖先 | `merge-base --is-ancestor` exit 0；实测仓含 tip | **PASS** |
| 2 | AF+PMSM → `meta.solver=axial_planes` | CLI：`meta.solver=axial_planes`；`mock=false`；`axial.converged=true` | **PASS** |
| 3 | 宣称冒烟值复核：T≈**2.330 Nm** / E≈**24.405 V** / **n_planes=4**（合理浮点误差；**不对标 ≤5%**） | `torque_nm=2.330476641855485`；`back_emf_v_peak=24.404694324719348`；`meta.n_planes=4` | **PASS**（相对宣称值偏差 ≪ 合理浮点；**未**宣称相对标杆 ≤5% 达标） |
| 4 | fixture `axial_pmsm_request.json` | `packages/solver-analytic/smoke/fixtures/axial_pmsm_request.json`（topology=AF machine_type=PMSM n_planes=4） | **PASS** |
| 5 | RF **mec** / **mock** / **acim** 未回归坏 | 三脚本均 exit 0；见下表 | **PASS** |

### AF+PMSM 关键字段（CLI）

```json
{
  "schema_version": "0.0.0-gate0",
  "meta": {
    "solver": "axial_planes",
    "elapsed_ms": 1.338,
    "mock": false,
    "n_planes": 4
  },
  "torque_nm": 2.330476641855485,
  "back_emf_v_peak": 24.404694324719348
}
```

### RF 回归摘要

| 路径 | 脚本 | 结果摘要 | 判定 |
| --- | --- | --- | --- |
| RF mec | `run_radial_pmsm_mec.py` | exit 0；`meta.solver=mec`；`mock=false`；T≈4.08585 Nm；E≈34.2295 V | **PASS** |
| RF mock | `run_radial_pmsm_mock.py` | exit 0；`meta.solver=mock`；`mock=true`；T=0.10368 Nm | **PASS** |
| RF acim | `run_radial_acim_equiv.py` | exit 0；`meta.solver=acim_equiv`；`mock=false`；T≈145.844 Nm | **PASS** |

## 未做 / 禁止宣称

- **未**勾选或宣称解析相对标杆 **≤5%** / FEM **≤3%**（仍待校准）。
- **未**以本项 compose API 绿关项（镜像未含本 tip 实现；记观察，不挡 CLI 主口径）。
- **未**测前端 / FEM / 几何（几何 `1bd8b51` 由并行任务）。

## 跟踪变更

| 项 | 变更 |
| --- | --- |
| Q3-P01 / Q3-1 解析侧 | **待测 → 通过**（tip `f2a2e94`） |
| P02–P07 | 本轮不改 |

## 结论

| 项 | 结论 |
| --- | --- |
| 解析 tip `f2a2e94`（Q3-1 / P01） | **PASS** |
| 对标 ≤5% | **未宣称**（禁止） |
