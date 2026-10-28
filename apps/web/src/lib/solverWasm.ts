/**
 * Wasm 解析内核 stub（Q2）。
 *
 * 未来包：`packages/solver-analytic-wasm`（Rust → wasm32，wasm-pack）。
 * 裁决：docs/drafts/Q2-材料与解析边界.md §4。
 *
 * 当前：包尚未到 → isWasmAvailable()=false；tryLoad 失败；solveWithWasm 返回 null。
 * 适配层据此降级到 sync → fixture/mock。
 */
import type { SolveRequest, SolveResult } from '@/types/solver'

let loadAttempted = false
let available = false

/** 是否已成功加载 Wasm 模块（Q2 stub 恒为 false） */
export function isWasmAvailable(): boolean {
  return available
}

/**
 * 尝试加载 Wasm glue。包未发布时立即失败并标记不可用。
 * @returns true 若可用
 */
export async function tryLoadWasm(): Promise<boolean> {
  if (loadAttempted) return available
  loadAttempted = true
  // TODO: dynamic import('@mo/solver-analytic-wasm') once packages/solver-analytic-wasm ships
  available = false
  return false
}

/**
 * 用 Wasm 求解。不可用时返回 null（勿 throw，便于降级）。
 */
export async function solveWithWasm(_request: SolveRequest): Promise<SolveResult | null> {
  const ok = await tryLoadWasm()
  if (!ok) return null
  // Placeholder for future wasm bindgen call with SolveRequest/SolveResult JSON
  throw new Error('solver-analytic-wasm not wired yet')
}
