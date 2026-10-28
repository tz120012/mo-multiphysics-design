/**
 * 解析快照序列化 — 拟写入 `.mems` `solver/analytic/` 的 JSON 形状。
 *
 * 挂点（勿在此真 PUT mems；由调用方 / Jobs worker 负责）：
 * - FE Wasm/sync 成功后 → putMems 或单文件更新 `solver/analytic/<id>.json`
 * - Jobs analytic 完成后 → resultRef / mems PUT
 *
 * 契约：docs/drafts/Q2-材料与解析边界.md §5；mems-schema-v1.md §5。
 * schemaVersion 与 solve schema 对齐（Q2 可沿用 0.0.0-gate0 或轻 bump 0.1.0-q2）。
 */
import type { SolveRequest, SolveResult } from '@/types/solver'
import { SOLVE_SCHEMA_VERSION } from '@/types/solver'

export interface AnalyticSnapshotDocument {
  /** 快照文档版本（可与 solve schema 同钉） */
  schemaVersion: string
  /** 写入时间 ISO */
  createdAt: string
  /** 产生路径：wasm | sync | fixture | mock | jobs */
  source: string
  request: SolveRequest
  result: SolveResult
  /** 可选工程 id，便于 mems 回写 */
  projectId?: string
}

/**
 * 把 request+result 序列化为拟写入 `.mems solver/analytic/` 的文档。
 * 不执行网络 I/O。
 */
export function buildAnalyticSnapshot(
  request: SolveRequest,
  result: SolveResult,
  opts?: { projectId?: string; source?: string },
): AnalyticSnapshotDocument {
  return {
    schemaVersion: SOLVE_SCHEMA_VERSION,
    createdAt: new Date().toISOString(),
    source: opts?.source ?? result.meta.source ?? (result.meta.mock ? 'mock' : 'unknown'),
    request,
    result,
    projectId: opts?.projectId,
  }
}

/** JSON 字符串（pretty），便于调试或后续 Blob 上传 */
export function serializeAnalyticSnapshot(doc: AnalyticSnapshotDocument): string {
  return `${JSON.stringify(doc, null, 2)}\n`
}
