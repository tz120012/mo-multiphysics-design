import { assertAcceptedMemsPackage, stampMemsPackageWriteVersion } from '@/lib/memsPackageVersion'
import { apiClient } from './client'
import {
  assertAcceptedMemsSchemaVersion,
  MEMS_SCHEMA_VERSION_WRITE,
  type HistoryCursorResponse,
  type HistoryListResponse,
  type MemsMeta,
  type Project,
  type ProjectCreate,
  type ProjectListResponse,
  type ProjectUpdate,
} from './types'

function acceptProject(project: Project): Project {
  assertAcceptedMemsSchemaVersion(project.memsSchemaVersion)
  return project
}

function acceptMemsMeta(meta: MemsMeta): MemsMeta {
  assertAcceptedMemsSchemaVersion(meta.memsSchemaVersion)
  return meta
}

/** OpenAPI ProjectCreate 尚无该字段；过渡期仍在创建/保存请求里发出写出版本。 */
function withWriteSchema<T extends object>(body: T): T & { memsSchemaVersion: typeof MEMS_SCHEMA_VERSION_WRITE } {
  return { ...body, memsSchemaVersion: MEMS_SCHEMA_VERSION_WRITE }
}

function schemaHeader(headers: unknown): string | undefined {
  if (!headers || typeof headers !== 'object') return undefined
  const bag = headers as { get?: (name: string) => unknown } & Record<string, unknown>
  const viaGet = typeof bag.get === 'function' ? bag.get('x-mems-schema-version') : undefined
  const raw = viaGet ?? bag['x-mems-schema-version']
  if (typeof raw === 'string' && raw.length > 0) return raw
  if (Array.isArray(raw) && typeof raw[0] === 'string' && raw[0].length > 0) return raw[0]
  return undefined
}

async function acceptMemsDownload(headers: unknown, blob: Blob): Promise<void> {
  const header = schemaHeader(headers)
  if (header) assertAcceptedMemsSchemaVersion(header)
  await assertAcceptedMemsPackage(new Uint8Array(await blob.arrayBuffer()))
}

async function fileWithWriteSchema(file: Blob | File): Promise<File> {
  const stamped = await stampMemsPackageWriteVersion(new Uint8Array(await file.arrayBuffer()))
  const name = file instanceof File && file.name ? file.name : 'project.mems'
  return new File([stamped], name, { type: file.type || 'application/zip' })
}

/** GET /projects */
export async function listProjects(params?: {
  limit?: number
  offset?: number
}): Promise<ProjectListResponse> {
  const { data } = await apiClient.get<ProjectListResponse>('/projects', { params })
  data.items.forEach(acceptProject)
  return data
}

/** POST /projects */
export async function createProject(body: ProjectCreate): Promise<Project> {
  const { data } = await apiClient.post<Project>('/projects', withWriteSchema(body))
  return acceptProject(data)
}

/** GET /projects/{projectId} */
export async function getProject(projectId: string): Promise<Project> {
  const { data } = await apiClient.get<Project>(`/projects/${projectId}`)
  return acceptProject(data)
}

/** PUT /projects/{projectId}（OpenAPI 为 put；勿用 PATCH） */
export async function updateProject(
  projectId: string,
  body: ProjectUpdate,
): Promise<Project> {
  const { data } = await apiClient.put<Project>(`/projects/${projectId}`, withWriteSchema(body))
  return acceptProject(data)
}

/** DELETE /projects/{projectId} → 204 */
export async function deleteProject(projectId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}`)
}

/**
 * GET /projects/{projectId}/mems/files/{path}
 * Q5-1 单成员读。path 为 zip 内相对路径（保留 `/`，不要整段 encode）。
 */
export async function getMemsFile(projectId: string, memberPath: string): Promise<Blob> {
  const response = await apiClient.get<Blob>(
    `/projects/${encodeURIComponent(projectId)}/mems/files/${memberPath}`,
    { responseType: 'blob' },
  )
  return response.data
}

/** GET /projects/{projectId}/mems → zip blob（Q1 可未接线） */
export async function getMems(projectId: string): Promise<Blob> {
  const response = await apiClient.get<Blob>(`/projects/${projectId}/mems`, {
    responseType: 'blob',
  })
  await acceptMemsDownload(response.headers, response.data)
  return response.data
}

/** PUT /projects/{projectId}/mems */
export async function putMems(projectId: string, file: Blob | File): Promise<MemsMeta> {
  const form = new FormData()
  form.append('file', await fileWithWriteSchema(file))
  const { data } = await apiClient.put<MemsMeta>(`/projects/${projectId}/mems`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return acceptMemsMeta(data)
}

/** POST /projects/{projectId}/mems/import */
export async function importMems(projectId: string, file: File): Promise<MemsMeta> {
  const form = new FormData()
  form.append('file', await fileWithWriteSchema(file))
  const { data } = await apiClient.post<MemsMeta>(
    `/projects/${projectId}/mems/import`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return acceptMemsMeta(data)
}

/** GET /projects/{projectId}/mems/export → zip blob */
export async function exportMems(projectId: string): Promise<Blob> {
  const response = await apiClient.get<Blob>(`/projects/${projectId}/mems/export`, {
    responseType: 'blob',
  })
  await acceptMemsDownload(response.headers, response.data)
  return response.data
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
