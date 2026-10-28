/**
 * Materials API 客户端 — GET list/get 对齐 OpenAPI Q2-1。
 * 契约：docs/drafts/Q2-材料与解析边界.md
 */
import { apiClient } from './client'
import type { Material, MaterialCategory, MaterialListResponse } from '@/types/materials'

/** GET /materials */
export async function listMaterials(params?: {
  category?: MaterialCategory
  includeDeleted?: boolean
}): Promise<MaterialListResponse> {
  const { data } = await apiClient.get<MaterialListResponse>('/materials', { params })
  return data
}

/** GET /materials/{materialId} */
export async function getMaterial(materialId: string): Promise<Material> {
  const { data } = await apiClient.get<Material>(`/materials/${materialId}`)
  return data
}
