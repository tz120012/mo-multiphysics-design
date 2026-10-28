/**
 * Wasm 解析内核（Q2）。
 *
 * 包：`packages/solver-analytic-wasm`（Rust → wasm32，wasm-pack --target web）。
 * 构建：`cd packages/solver-analytic-wasm && ./build.sh` → `pkg/`（仓库可含构建产物；亦可本地 ./build.sh）。
 * 裁决：docs/drafts/Q2-材料与解析边界.md §4。
 *
 * 未构建 / 加载失败 → isWasmAvailable()=false；solveWithWasm 返回 null，适配层降级 sync/fixture。
 */
import type { SolveRequest, SolveResult } from '@/types/solver'

type WasmModule = {
  default: (input?: RequestInfo | URL | BufferSource | WebAssembly.Module) => Promise<unknown>
  solve_json: (input: string) => string
}

let loadAttempted = false
let available = false
let solveJsonFn: ((input: string) => string) | null = null

/** 是否已成功加载 Wasm 模块 */
export function isWasmAvailable(): boolean {
  return available
}

/**
 * 尝试加载 Wasm glue（优先加载已提交 pkg/；缺失时可 ./build.sh）。
 * @returns true 若可用
 */
export async function tryLoadWasm(): Promise<boolean> {
  if (loadAttempted) return available
  loadAttempted = true
  try {
    // Alias → packages/solver-analytic-wasm/pkg (vite.config.ts); fails soft if pkg missing.
    const mod = (await import(
      /* @vite-ignore */
      '@mo/solver-analytic-wasm/solver_analytic_wasm.js'
    )) as WasmModule
    await mod.default()
    if (typeof mod.solve_json !== 'function') {
      available = false
      return false
    }
    solveJsonFn = mod.solve_json
    available = true
    return true
  } catch {
    available = false
    solveJsonFn = null
    return false
  }
}

/**
 * 用 Wasm 求解。不可用或求解失败时返回 null（勿 throw，便于降级）。
 */
export async function solveWithWasm(request: SolveRequest): Promise<SolveResult | null> {
  const ok = await tryLoadWasm()
  if (!ok || !solveJsonFn) return null
  try {
    const raw = solveJsonFn(JSON.stringify(request))
    const result = JSON.parse(raw) as SolveResult & { error?: { code?: string; message?: string } }
    if (result && typeof result === 'object' && 'error' in result && result.error) {
      return null
    }
    return result as SolveResult
  } catch {
    return null
  }
}
