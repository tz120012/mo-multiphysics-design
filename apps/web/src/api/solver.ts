/**
 * 可选同步解析端 — POST /solver/analytic/solve
 * 对齐 OpenAPI AnalyticSolveRequest/Result（镜像 solve.schema.json）。
 * 未实现可 501；FE 降级序见 docs/drafts/Q2-材料与解析边界.md §3.3。
 */
import { apiClient } from './client'
import type { SolveRequest, SolveResult } from '@/types/solver'

/** POST /solver/analytic/solve — body=SolveRequest，响应=SolveResult */
export async function postAnalyticSolve(req: SolveRequest): Promise<SolveResult> {
  const { data } = await apiClient.post<SolveResult>('/solver/analytic/solve', req)
  return data
}
