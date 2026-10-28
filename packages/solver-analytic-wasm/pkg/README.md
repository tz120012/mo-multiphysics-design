# solver-analytic-wasm

Rust → `wasm32-unknown-unknown` 解析内核。JSON 契约对齐  
`packages/solver-analytic/api/solve.schema.json`（`SolveRequest` → `SolveResult`）。

Python 包 `packages/solver-analytic` 仍是**金标**；本 crate 为浏览器路径（架构 #1）。  
**不对标 ≤5%**。`meta.note` 标明 wasm stub vs python golden。

## 导出

| 符号 | 说明 |
| --- | --- |
| `solve_json(input: string): string` | 入参 / 出参均为 JSON 字符串；错误时 `{error:{code,message}, meta:{wasm:true,…}}` |

支持：

| 拓扑 | 机型 | `meta.solver` | 说明 |
| --- | --- | --- | --- |
| RF | PMSM | `mec` | 非线性串联 MEC |
| RF | BLDC | `mec` | PMSM 近似 + BLDC 系数 |
| RF | ACIM | `acim_equiv` | 等效电路 |
| AF | PMSM | `axial_planes` | 同心分环 + 每环串联 MEC（Q4+-4 stub） |
| — | — | `mock` | 仅 RF+PMSM Gate0 mock |

`meta.wasm=true`。AF 非 PMSM → 清晰 `not_implemented`（指向 sync/Jobs Python）。

材料读取序与 Python 一致：内联 → `curves` → `meta` → 默认。

## 构建

```bash
# 依赖：rustup + wasm32-unknown-unknown + wasm-pack
rustup target add wasm32-unknown-unknown
cargo install wasm-pack

cd packages/solver-analytic-wasm
./build.sh
# → ./pkg/  solver_analytic_wasm.js + solver_analytic_wasm_bg.wasm
```

原生测试：

```bash
cargo test
# 覆盖 RF PMSM/ACIM + AF PMSM fixture；RF 路径不破
```

若仓库已提交 `pkg/`，FE 可直接加载，无需先 build。

## 前端 import（apps/web）

```ts
// 相对路径（Vite）
import init, { solve_json } from "../../../packages/solver-analytic-wasm/pkg/solver_analytic_wasm.js";

await init();
const result = JSON.parse(solve_json(JSON.stringify(solveRequest)));
if (result.error) throw new Error(result.error.message);
// RF: result.meta.solver === "mec" | "acim_equiv" | "mock"
// AF+PMSM: result.meta.solver === "axial_planes"
// result.meta.wasm === true
```

可选 `package.json`：`"@mo/solver-analytic-wasm": "file:../../packages/solver-analytic-wasm/pkg"`（需 `pkg/` 存在）。

样例：`fixtures/radial_pmsm_request.json`、`fixtures/radial_acim_request.json`、`fixtures/axial_pmsm_request.json`（与 Python smoke 同形）。

AF Wasm 演示入口与局限：[`docs/drafts/Q4+-4-AF-Wasm.md`](../../docs/drafts/Q4+-4-AF-Wasm.md)。

## 目录

```
solver-analytic-wasm/
  Cargo.toml
  build.sh
  src/{lib,materials,pmsm,acim,axial_planes}.rs
  fixtures/
  pkg/          # wasm-pack --target web 产物（可提交）
```
