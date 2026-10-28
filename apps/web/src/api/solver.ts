/**
 * 同步解析端 — POST /solver/analytic/solve?solver=mec|mock
 * tip 8b71df1：已接线 Python 金标（不再 501）；query `solver` 默认 mec。
 * 失败（网络/404/501 等）时 FE 降级 fixture/mock，见 docs/drafts/Q2-材料与解析边界.md §3.3。
 */
import { apiClient } from './client'
import type { SolveRequest, SolveResult } from '@/types/solver'

/** POST /solver/analytic/solve — body=SolveRequest，query solver，响应=SolveResult */
export async function postAnalyticSolve(
  req: SolveRequest,
  opts?: { solver?: 'mec' | 'mock' },
): Promise<SolveResult> {
  const solver = opts?.solver ?? 'mec'
  const { data } = await apiClient.post<SolveResult>('/solver/analytic/solve', req, {
    params: { solver },
  })
  return data
}
