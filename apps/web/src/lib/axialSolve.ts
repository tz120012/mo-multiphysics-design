/**
 * 轴向 AF-PMSM 解析适配（Q3-2）。
 *
 * 架构 docs/drafts/Q3-轴向与FEM边界.md §2.2：
 * AF 交互主路径 = sync 或 Jobs analytic；Wasm AF 仍无。
 * 本 tip 降级序：**优先 sync**，失败再 fixture（stub / 本地金标结果）。
 * 禁止走 Wasm（AF 会硬失败）。勿破坏 RF `lib/analyticSolve.ts`（Wasm→sync→fixture）。
 *
 * 金标量级参考（Mo-解析 tip f2a2e94 smoke）：
 * T≈2.330 Nm，E≈24.405 V，Pcu≈19.77，Pfe≈42.24；meta.solver=axial_planes，mock=false。
 */
import { isAxiosError } from 'axios'
import { postAnalyticSolve } from '@/api/solver'
import type { SolveBackend, SolveRequest, SolveResult } from '@/types/solver'
import { SOLVE_SCHEMA_VERSION } from '@/types/solver'

/** Mo-解析 smoke 请求（金标入参） */
export const AF_REQUEST_URL = '/solver/axial_pmsm_request.json'
/** 本地 smoke 结果快照（sync 不可达时优先） */
const AF_RESULT_URL = '/solver/axial_pmsm_result.json'
/** tip c59ccf3 stub（终极兜底） */
const AF_STUB_RESULT_URL = '/solver/axial_pmsm_stub_result.json'
const AF_STUB_REQUEST_URL = '/solver/axial_pmsm_stub_request.json'

let cachedFixture: SolveResult | null = null
let lastBackend: SolveBackend | null = null

export function getAxialSolveBackend(): SolveBackend | null {
  return lastBackend
}

function nowMs(): number {
  return typeof performance !== 'undefined' ? performance.now() : Date.now()
}

function assertAxialPmsm(request: SolveRequest): void {
  if (request.schema_version !== SOLVE_SCHEMA_VERSION) {
    throw new Error(
      `不支持的 schema_version：${request.schema_version}（仅 ${SOLVE_SCHEMA_VERSION}）`,
    )
  }
  if (request.topology !== 'AF') {
    throw new Error(`axialSolve 仅支持 AF，当前 topology=${request.topology}`)
  }
  if (request.machine_type !== 'PMSM') {
    throw new Error(`axialSolve MVP 仅 AF-PMSM，当前 machine_type=${request.machine_type}`)
  }
}

function tagSource(result: SolveResult, source: SolveBackend, elapsedMs?: number): SolveResult {
  const meta = {
    ...result.meta,
    source,
    elapsed_ms: elapsedMs ?? result.meta.elapsed_ms,
  }
  if (source === 'fixture' || source === 'mock') {
    meta.mock = true
  }
  return { ...result, meta }
}

export async function loadAxialSampleRequest(): Promise<SolveRequest> {
  const res = await fetch(AF_REQUEST_URL)
  if (!res.ok) {
    const stub = await fetch(AF_STUB_REQUEST_URL)
    if (!stub.ok) throw new Error(`AF request ${res.status}`)
    return (await stub.json()) as SolveRequest
  }
  return (await res.json()) as SolveRequest
}

async function loadFixtureResult(): Promise<SolveResult> {
  if (cachedFixture) return structuredClone(cachedFixture)
  for (const url of [AF_RESULT_URL, AF_STUB_RESULT_URL]) {
    try {
      const res = await fetch(url)
      if (!res.ok) continue
      const data = (await res.json()) as SolveResult
      cachedFixture = data
      return structuredClone(data)
    } catch {
      /* try next */
    }
  }
  throw new Error('无法加载 AF fixture（axial_pmsm_result / stub_result）')
}

async function trySyncSolve(request: SolveRequest): Promise<SolveResult | null> {
  try {
    // 后端按 topology 路由到 axial_planes；query solver=mec 表示真核（非 mock）
    const result = await postAnalyticSolve(request, { solver: 'mec' })
    return tagSource(result, 'sync')
  } catch (err) {
    if (isAxiosError(err)) {
      const status = err.response?.status
      if (status === 404 || status === 501 || status == null || status >= 400) {
        return null
      }
    }
    return null
  }
}

/**
 * AF 求解：sync → fixture。不打 Wasm。
 */
export async function solveAxial(request: SolveRequest): Promise<SolveResult> {
  assertAxialPmsm(request)
  const t0 = nowMs()

  const syncResult = await trySyncSolve(request)
  if (syncResult) {
    lastBackend = 'sync'
    return {
      ...syncResult,
      meta: {
        ...syncResult.meta,
        elapsed_ms: syncResult.meta.elapsed_ms || nowMs() - t0,
      },
    }
  }

  const base = await loadFixtureResult()
  const tagged = tagSource(base, 'fixture', nowMs() - t0)
  tagged.meta = {
    ...tagged.meta,
    note:
      tagged.meta.note ??
      'AF：sync 不可达，fixture 兜底（待 sync/Jobs 金标常驻）。Wasm AF 未落地。',
  }
  lastBackend = 'fixture'
  return tagged
}

/** @deprecated 用 solveAxial；保留别名以免旧引用断裂 */
export const solveAxialFixture = solveAxial
