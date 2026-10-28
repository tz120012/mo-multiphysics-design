import { apiClient } from './client'
import type {
  HistoryCursorResponse,
  HistoryListResponse,
  MemsMeta,
  Project,
  ProjectCreate,
  ProjectListResponse,
  ProjectUpdate,
} from './types'

/** GET /projects */
export async function listProjects(params?: {
  limit?: number
  offset?: number
}): Promise<ProjectListResponse> {
  const { data } = await apiClient.get<ProjectListResponse>('/projects', { params })
  return data
}

/** POST /projects */
export async function createProject(body: ProjectCreate): Promise<Project> {
  const { data } = await apiClient.post<Project>('/projects', body)
  return data
}

/** GET /projects/{projectId} */
export async function getProject(projectId: string): Promise<Project> {
  const { data } = await apiClient.get<Project>(`/projects/${projectId}`)
  return data
}

/** PUT /projects/{projectId}（OpenAPI 为 put；勿用 PATCH） */
export async function updateProject(
  projectId: string,
  body: ProjectUpdate,
): Promise<Project> {
  const { data } = await apiClient.put<Project>(`/projects/${projectId}`, body)
  return data
}

/** DELETE /projects/{projectId} → 204 */
export async function deleteProject(projectId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}`)
}

/** GET /projects/{projectId}/mems → zip blob（Q1 可未接线） */
export async function getMems(projectId: string): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/projects/${projectId}/mems`, {
    responseType: 'blob',
  })
  return data
}

/** PUT /projects/{projectId}/mems */
export async function putMems(projectId: string, file: Blob | File): Promise<MemsMeta> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.put<MemsMeta>(`/projects/${projectId}/mems`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/** POST /projects/{projectId}/mems/import */
export async function importMems(projectId: string, file: File): Promise<MemsMeta> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<MemsMeta>(
    `/projects/${projectId}/mems/import`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

/** GET /projects/{projectId}/mems/export → zip blob */
export async function exportMems(projectId: string): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/projects/${projectId}/mems/export`, {
    responseType: 'blob',
  })
  return data
}

/** GET /projects/{projectId}/history */
export async function listHistory(projectId: string): Promise<HistoryListResponse> {
  const { data } = await apiClient.get<HistoryListResponse>(`/projects/${projectId}/history`)
  return data
}

/** POST /projects/{projectId}/history/undo */
export async function undoHistory(projectId: string): Promise<HistoryCursorResponse> {
  const { data } = await apiClient.post<HistoryCursorResponse>(
    `/projects/${projectId}/history/undo`,
  )
  return data
}

/** POST /projects/{projectId}/history/redo */
export async function redoHistory(projectId: string): Promise<HistoryCursorResponse> {
  const { data } = await apiClient.post<HistoryCursorResponse>(
    `/projects/${projectId}/history/redo`,
  )
  return data
}
