/**
 * Ambient types for dynamic import of solver-analytic-wasm glue.
 * Vite alias → packages/solver-analytic-wasm/pkg; runtime soft-fails if missing.
 */
declare module '@mo/solver-analytic-wasm/solver_analytic_wasm.js' {
  export type InitInput =
    | RequestInfo
    | URL
    | Response
    | BufferSource
    | WebAssembly.Module

  export default function init(
    module_or_path?:
      | { module_or_path: InitInput | Promise<InitInput> }
      | InitInput
      | Promise<InitInput>,
  ): Promise<unknown>

  /** SolveRequest JSON string → SolveResult JSON string (or error envelope). */
  export function solve_json(input: string): string
}
