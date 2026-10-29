import { apiClient } from './client'

/**
 * POST /geometry/rebuild
 * 同步（非 Job）。baseURL 已含 /api/v1。
 * 契约：docs/drafts/Q6-UEM与几何rebuild契约.md
 */
export interface GeometryRebuildRequest {
  topology: 'RF' | 'AF'
  machineType?: string
  params: Record<string, unknown>
}

export async function postGeometryRebuild(body: GeometryRebuildRequest): Promise<unknown> {
  const { data } = await apiClient.post<unknown>('/geometry/rebuild', body)
  return data
}
