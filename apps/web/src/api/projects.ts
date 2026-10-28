import type {
  HistoryCursorResponse,
  HistoryListResponse,
  MemsMeta,
  Project,
  ProjectCreate,
  ProjectListResponse,
  ProjectUpdate,
} from './types'

const NOT_WIRED = 'not wired'

/** GET /projects */
export async function listProjects(_params?: {
  limit?: number
  offset?: number
}): Promise<ProjectListResponse> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** POST /projects */
export async function createProject(_body: ProjectCreate): Promise<Project> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** GET /projects/{projectId} */
export async function getProject(_projectId: string): Promise<Project> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** PUT /projects/{projectId}（OpenAPI 为 put；非 patch） */
export async function updateProject(
  _projectId: string,
  _body: ProjectUpdate,
): Promise<Project> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** DELETE /projects/{projectId} → 204 */
export async function deleteProject(_projectId: string): Promise<void> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** GET /projects/{projectId}/mems → zip blob */
export async function getMems(_projectId: string): Promise<Blob> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** PUT /projects/{projectId}/mems */
export async function putMems(_projectId: string, _file: Blob | File): Promise<MemsMeta> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** POST /projects/{projectId}/mems/import */
export async function importMems(_projectId: string, _file: File): Promise<MemsMeta> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** GET /projects/{projectId}/mems/export → zip blob */
export async function exportMems(_projectId: string): Promise<Blob> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** GET /projects/{projectId}/history */
export async function listHistory(_projectId: string): Promise<HistoryListResponse> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** POST /projects/{projectId}/history/undo */
export async function undoHistory(_projectId: string): Promise<HistoryCursorResponse> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** POST /projects/{projectId}/history/redo */
export async function redoHistory(_projectId: string): Promise<HistoryCursorResponse> {
  return Promise.reject(new Error(NOT_WIRED))
}
