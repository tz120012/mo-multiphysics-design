import { isAxiosError } from 'axios'
import { postGeometryRebuild, type GeometryRebuildRequest } from '@/api/geometry'
import type { MeshDescriptor, MeshPrimitive } from '@/types/mesh'

/**
 * 几何重建适配器。只认 HTTP 200 且带可用 meshDescriptor + geometrySummary。
 * 不读取 public/mesh，不用 fixture JSON 冒充 200。
 * 失败由调用方另行降级并打标。
 */

export const REBUILD_DEBOUNCE_MS = 200

export interface GeometrySummarySlice {
  poles: number
  slots: number
  stack_length_m: number
  airgap_m: number
  rotor_od_m: number
  stator_id_m: number
  [key: string]: unknown
}

export interface LiveRebuild {
  params: Record<string, unknown>
  meshDescriptor: MeshDescriptor
  geometrySummary: GeometrySummarySlice
  pipelineEntry?: Record<string, unknown>
  /** 几何包可选信封；缺省不挡成功。 */
  paramsHash?: string
}

export type RebuildResult =
  | { ok: true; live: LiveRebuild }
  | { ok: false; status: number | null; message: string }

const SUMMARY_KEYS = [
  'poles',
  'slots',
  'stack_length_m',
  'airgap_m',
  'rotor_od_m',
  'stator_id_m',
] as const

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

function isKnownPrimitive(value: unknown): value is MeshPrimitive {
  if (!isRecord(value)) return false
  if (value.type !== 'ring' && value.type !== 'sector') return false
  if (typeof value.name !== 'string') return false
  return typeof value.innerRadius === 'number' && typeof value.outerRadius === 'number'
}

export function isUsableMeshDescriptor(value: unknown): value is MeshDescriptor {
  if (!isRecord(value)) return false
  if (value.kind !== 'radial' && value.kind !== 'axial') return false
  if (!isRecord(value.units) || !isRecord(value.meta)) return false
  if (!Array.isArray(value.primitives) || value.primitives.length === 0) return false
  return value.primitives.some(isKnownPrimitive)
}

export function isGeometrySummarySlice(value: unknown): value is GeometrySummarySlice {
  if (!isRecord(value)) return false
  return SUMMARY_KEYS.every((key) => typeof value[key] === 'number' && Number.isFinite(value[key]))
}

export function meshFingerprint(descriptor: MeshDescriptor | null): string {
  if (!descriptor) return ''
  return JSON.stringify([descriptor.kind, descriptor.meta, descriptor.primitives])
}

/** 容忍 paramsHash 及其它额外字段；最小集仍是 params + meshDescriptor + geometrySummary。 */
export function parseLiveRebuild(data: unknown): LiveRebuild | null {
  if (!isRecord(data)) return null
  if (!isRecord(data.params)) return null
  if (!isUsableMeshDescriptor(data.meshDescriptor)) return null
  if (!isGeometrySummarySlice(data.geometrySummary)) return null
  const paramsHash = typeof data.paramsHash === 'string' && data.paramsHash ? data.paramsHash : undefined
  const pipelineEntry = isRecord(data.pipelineEntry) ? data.pipelineEntry : undefined
  return {
    params: data.params,
    meshDescriptor: data.meshDescriptor,
    geometrySummary: data.geometrySummary,
    ...(pipelineEntry ? { pipelineEntry } : {}),
    ...(paramsHash ? { paramsHash } : {}),
  }
}

function digMessage(data: unknown): string {
  if (!isRecord(data)) return ''
  if (typeof data.message === 'string') return data.message
  const detail = data.detail
  if (typeof detail === 'string') return detail
  if (isRecord(detail) && typeof detail.message === 'string') return detail.message
  return ''
}

function formatAxios(err: unknown): { status: number | null; message: string } {
  if (!isAxiosError(err)) {
    return { status: null, message: err instanceof Error ? err.message : String(err) }
  }
  const status = err.response?.status ?? null
  const detail = digMessage(err.response?.data)
  if (status == null) return { status: null, message: detail || '网络不可达' }
  return { status, message: detail ? `HTTP ${status} ${detail}` : `HTTP ${status}` }
}

export async function requestGeometryRebuild(body: GeometryRebuildRequest): Promise<RebuildResult> {
  try {
    const data = await postGeometryRebuild(body)
    const live = parseLiveRebuild(data)
    if (!live) {
      return { ok: false, status: 200, message: '响应缺少可用 meshDescriptor 或 geometrySummary' }
    }
    return { ok: true, live }
  } catch (err) {
    const formatted = formatAxios(err)
    return { ok: false, status: formatted.status, message: formatted.message }
  }
}
