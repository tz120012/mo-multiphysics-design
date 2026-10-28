# Q4+-4 AF Wasm — 可演示最小路径（路径 A）

| 项 | 值 |
| --- | --- |
| 状态 | **路径 A 已落地**：Wasm AF+PMSM 多平面 stub 可演示 |
| 日期 | 2026-10-28（Asia/Shanghai） |
| 作者 | Mo-解析（执行助手） |
| 基线 | `10d3ff9` |
| 包 | `packages/solver-analytic-wasm/` |
| 金标 | Python `packages/solver-analytic/axial_planes/`（sync / Jobs） |
| 锁定参考 | [`Q3-轴向与FEM边界.md`](./Q3-轴向与FEM边界.md) §2.2（AF Wasm = stretch / fast-follow） |

> **不对标 ≤5%**。本路径为浏览器可演示 stub；数值以 Python 金标为准。禁止宣称相对标杆达标。

---

## 1. 决策

Motor 允许「可演示」或「书面降级」二选一。本轮选 **路径 A**：在 `solver-analytic-wasm` 增加 AF+PMSM 同心分环 + 简化串联磁路，同 `SolveRequest`/`SolveResult` 契约。

| 字段 | 值 |
| --- | --- |
| `topology` | `AF` |
| `machine_type` | `PMSM` |
| `meta.solver` | `axial_planes` |
| `meta.wasm` | `true` |
| `meta.mock` | `false` |
| `meta.note` | 标明 **wasm stub vs python golden** |

AF 非 PMSM / 其他拓扑：返回 `not_implemented`，文案指向 sync/Jobs Python。

---

## 2. 演示入口

### 2.1 原生（无浏览器）

```bash
cd packages/solver-analytic-wasm
cargo test
# 关键测试：af_pmsm_fixture_finite、pmsm_fixture_finite、acim_fixture_finite
```

或在 Rust/宿主侧：

```text
solve_json(fixtures/axial_pmsm_request.json)
→ torque_nm / back_emf_v_peak 有限非 NaN；meta.solver=axial_planes；meta.wasm=true
```

Fixture 与 Python smoke 同形：`packages/solver-analytic/smoke/fixtures/axial_pmsm_request.json`  
（Wasm 包内副本：`packages/solver-analytic-wasm/fixtures/axial_pmsm_request.json`）。

### 2.2 浏览器（FE 已有加载层）

1. 确保 `pkg/` 已构建（见 §4）。
2. `apps/web` 经 `solverWasm.ts` → `solve_json`；适配层 `analyticSolve.ts` 降级序不变（**本任务不改 FE**）。
3. 将 `SolveRequest.topology='AF'`、`machine_type='PMSM'` 送入 Wasm；成功则 `meta.solver=axial_planes`。
4. 若需金标对照：同一请求走 sync `POST /solver/analytic/solve`（Python `axial_planes`）。

AF 交互主路径在 Q3 锁定中仍可为 sync/Jobs；Wasm AF 为 stretch 演示，不替代金标。

---

## 3. 算法与局限

| 项 | 说明 |
| --- | --- |
| 几何 | 内外径分环（默认 `n_planes=4`）；`rotor_od_m`/`stator_id_m` 作外/内直径 stub 映射（与 Python 一致） |
| 磁路 | 每环独立串联单极 MEC（PM→气隙→齿→定/转子轭）；解析 μ(B)；环间无径向耦合 |
| 输出 | `torque_nm`、`back_emf_v_peak`、`losses_w`、`inductance_h`；`meta.axial.planes[]` |
| 多盘 | `disk_count` 仅 meta；转矩按单气隙等效 |
| 精度 | **不对标 ≤5%**；禁止与 golden 做关门精度断言 |
| 未覆盖 | AF+BLDC / AF+ACIM；完整漏磁 / 端部 / 标定曲线 |

源码：`packages/solver-analytic-wasm/src/axial_planes.rs`（简化移植 Python `axial_planes/{geometry,pmsm}.py`）。

---

## 4. 构建 `pkg/`

```bash
rustup target add wasm32-unknown-unknown
# 若无 wasm-pack：cargo install wasm-pack
cd packages/solver-analytic-wasm
./build.sh
# → pkg/solver_analytic_wasm.js + solver_analytic_wasm_bg.wasm
```

无 `wasm-pack` 时不要手改 `pkg/`；装好后按上式重建。本轮若环境有 `wasm-pack`，执行助手已跑 `./build.sh` 更新产物。

---

## 5. 验证（给 Motor / 测试）

| 命令 | 期望 |
| --- | --- |
| `cd packages/solver-analytic-wasm && cargo test` | 全绿；含 AF+PMSM；RF PMSM/ACIM 仍过 |
| （可选）`./build.sh` | `pkg/` 更新；FE 可加载 |

交测一句话：**Wasm AF+PMSM 用 `fixtures/axial_pmsm_request.json` 经 `solve_json` 得有限 T/E，`meta.solver=axial_planes` 且 `meta.wasm=true`；RF 单测不破；数值以 Python 金标为准，不对标 ≤5%。**

---

## 6. 改动文件（本任务）

- `packages/solver-analytic-wasm/src/axial_planes.rs`（新建）
- `packages/solver-analytic-wasm/src/lib.rs`（路由 AF+PMSM + 测试）
- `packages/solver-analytic-wasm/fixtures/axial_pmsm_request.json`（新建）
- `packages/solver-analytic-wasm/README.md`
- `packages/solver-analytic-wasm/pkg/`（有 wasm-pack 则更新）
- `docs/drafts/Q4+-4-AF-Wasm.md`（本文件）

未改：`docs/01`、`docs/02`、FE 大改、其他项目。**未 git commit。**

---

## 7. 关闭项

- Q4+-D2（AF Wasm 余项）：以路径 A 可演示关闭；书面降级（路径 B）不采用。
