# solver-analytic-wasm

Rust → `wasm32-unknown-unknown` 径向解析（Q2）。JSON 契约对齐  
`packages/solver-analytic/api/solve.schema.json`（`SolveRequest` → `SolveResult`）。

Python 包 `packages/solver-analytic` 仍是**金标**；本 crate 为浏览器主路径（架构 #1）。  
**不对标 ≤5%**。`meta.note` 标明 wasm stub vs python golden 对拍中。

## 导出

| 符号 | 说明 |
| --- | --- |
| `solve_json(input: string): string` | 入参 / 出参均为 JSON 字符串；错误时 `{error:{code,message}, meta:{wasm:true,…}}` |

支持：`RF+PMSM`（非线性串联 MEC，`meta.solver=mec`）、`RF+BLDC`、`RF+ACIM`（`meta.solver=acim_equiv`）、`solver=mock`。

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
```

若仓库已提交 `pkg/`（约 160KB），FE 可直接加载，无需先 build。

## 前端 import（apps/web）

```ts
// 相对路径（Vite）
import init, { solve_json } from "../../../packages/solver-analytic-wasm/pkg/solver_analytic_wasm.js";

await init();
// 或: await init(new URL("../../../packages/solver-analytic-wasm/pkg/solver_analytic_wasm_bg.wasm", import.meta.url));
const result = JSON.parse(solve_json(JSON.stringify(solveRequest)));
if (result.error) throw new Error(result.error.message);
// result.meta.solver === "mec" | "acim_equiv" | "mock"
// result.meta.wasm === true
```

可选 `package.json`：`"@mo/solver-analytic-wasm": "file:../../packages/solver-analytic-wasm/pkg"`（需 `pkg/` 存在）。

样例：`fixtures/radial_pmsm_request.json`、`fixtures/radial_acim_request.json`（与 Python smoke 同形）。

## 目录

```
solver-analytic-wasm/
  Cargo.toml
  build.sh
  src/{lib,materials,pmsm,acim}.rs
  fixtures/
  pkg/          # wasm-pack --target web 产物（可提交）
```
