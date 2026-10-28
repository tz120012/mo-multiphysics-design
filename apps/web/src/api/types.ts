/**
 * 手写最小类型，对齐 docs/drafts/openapi-v1.yaml（1.0.0-draft）
 * 与 docs/drafts/mems-schema-v1.md（memsSchemaVersion: 1.0.0-draft）
 */

/** 径向 RF / 轴向 AF */
export type Topology = 'RF' | 'AF'

/** 机型枚举 */
export type MachineType = 'BLDC' | 'PMSM' | 'ACIM'

/** 当前 MEMS 包 schema 版本（契约锁定） */
export const MEMS_SCHEMA_VERSION = '1.0.0-draft' as const
export type MemsSchemaVersion = typeof MEMS_SCHEMA_VERSION

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  tokenType: string
}

export interface AuthUser {
  id: string
  username: string
  displayName?: string
}

export interface Project {
  id: string
  name: string
  topology: Topology
  machineType: MachineType
  memsSchemaVersion: string
  createdAt: string
  updatedAt: string
}

export interface ProjectCreate {
  name: string
  topology: Topology
  machineType: MachineType
  units?: Record<string, unknown>
}

/**
 * OpenAPI 中 PUT /projects/{id} 的 body 复用 ProjectCreate。
 * 命名 ProjectUpdate 便于前端语义；字段与 ProjectCreate 一致。
 */
export type ProjectUpdate = ProjectCreate

export interface ProjectListResponse {
  items: Project[]
  total: number
}

export interface MemsMeta {
  projectId: string
  memsSchemaVersion: string
  sizeBytes: number
  checksumSha256: string
  updatedAt: string
}

/** Q1-6 commandType 最小集（见 docs/drafts/history-契约-q1-6.md） */
export type HistoryCommandType =
  | 'geometry.params.set'
  | 'project.meta.set'
  | 'noop'

export interface HistoryEntry {
  id: string
  commandType: string
  summary: string
  createdAt: string
  /** 真实命令必有；正向参数，须可重放 */
  payload?: Record<string, unknown>
  /** 推荐：撤销所需（inverse of payload）；缺则 FE 用 payload.before 快照 */
  inverse?: Record<string, unknown>
}

export interface HistoryListResponse {
  entries: HistoryEntry[]
  cursor: number
}

export interface HistoryCursorResponse {
  cursor: number
  entry: HistoryEntry
}

/** .mems 内 history/stack.json 落盘形状 */
export const HISTORY_STACK_SCHEMA_VERSION = '0.1.0-q1-history' as const

export interface HistoryStackDocument {
  schemaVersion: typeof HISTORY_STACK_SCHEMA_VERSION | string
  entries: HistoryEntry[]
  cursor: number
}

/** UI 展示用 label（值仍为枚举） */
export const TOPOLOGY_LABELS: Record<Topology, string> = {
  RF: '径向磁通',
  AF: '轴向磁通',
}

export const MACHINE_TYPE_LABELS: Record<MachineType, string> = {
  BLDC: 'BLDC',
  PMSM: 'PMSM',
  ACIM: 'ACIM',
}
