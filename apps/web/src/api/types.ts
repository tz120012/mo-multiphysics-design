/**
 * 手写最小类型，对齐 docs/drafts/openapi-v1.yaml（1.0.0；Q5-5）
 * 与 docs/drafts/mems-schema-v1.md（memsSchemaVersion: 1.0.0）。
 *
 * 展示常量钉 `1.0.0`：后端 tip `8d9fc3b`，架构 tip `4b553f5`
 * （`docs/drafts/Q5-5-契约1.0.0钉死.md`）。
 * 读 / 接受仍双接受 `1.0.0` 与 `1.0.0-draft`。
 * 新写入 / 保存只发出 `1.0.0`。
 * 钉 `1.0.0` ≠ MVP，≠ git tag `v1.0.0`。
 */

/** 径向 RF / 轴向 AF */
export type Topology = 'RF' | 'AF'

/** 机型枚举 */
export type MachineType = 'BLDC' | 'PMSM' | 'ACIM'

/** 当前 MEMS 包 schema 版本。tip `8d9fc3b` / `4b553f5`；钉版本 ≠ MVP / tag。 */
export const MEMS_SCHEMA_VERSION = '1.0.0' as const
export type MemsSchemaVersion = typeof MEMS_SCHEMA_VERSION

/** 读侧接受的整包版本（Q5-5 过渡仍双接受 draft）。 */
export const MEMS_SCHEMA_VERSIONS_ACCEPTED = ['1.0.0', '1.0.0-draft'] as const
export type MemsSchemaVersionAccepted = (typeof MEMS_SCHEMA_VERSIONS_ACCEPTED)[number]

/** 新建工程与 mems 保存写出的版本，与展示钉相同。 */
export const MEMS_SCHEMA_VERSION_WRITE = MEMS_SCHEMA_VERSION

export function isAcceptedMemsSchemaVersion(
  version: string | null | undefined,
): version is MemsSchemaVersionAccepted {
  return (MEMS_SCHEMA_VERSIONS_ACCEPTED as readonly string[]).includes(version ?? '')
}

export function assertAcceptedMemsSchemaVersion(
  version: string | null | undefined,
): asserts version is MemsSchemaVersionAccepted {
  if (!isAcceptedMemsSchemaVersion(version)) {
    throw new Error(
      `memsSchemaVersion ${JSON.stringify(version ?? null)} is not accepted; Q5-5 (tips 8d9fc3b / 4b553f5) accepts "1.0.0" and "1.0.0-draft"`,
    )
  }
}

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

/** Jobs — 对齐 openapi Job / JobCreate / FemJobPayload（OpenAPI Job 不含 payload） */
export type JobType = 'analytic' | 'fem' | 'optimize' | 'drive'

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'

export interface ApiErrorBody {
  code: string
  message: string
  details?: Record<string, unknown>
}

export type FemDim = '2d' | '3d'
export type FemSolverKernel = 'elmer' | 'getdp'

/**
 * Q3 FEM 作业载荷。必填：topology, machineType, dim, solverKernel,
 * meshProfile, operatingPoint, materials。
 */
export interface FemJobPayload {
  projectId?: string
  topology: Topology
  machineType: MachineType
  dim: FemDim
  solverKernel: FemSolverKernel
  /** e.g. rf_pmsm_2d_default | af_pmsm_3d_min */
  meshProfile: string
  operatingPoint: Record<string, unknown>
  materials: Record<string, unknown> | Record<string, unknown>[]
  templateId?: string
}


/** Drive modes — packages/solver-drive */
export type DriveMode = 'bldc_square' | 'pmsm_foc' | 'acim_vf' | 'acim_foc'

export interface DriveJobPayload {
  mode: DriveMode | 'efficiency_map'
  machineType: MachineType
  operatingPoint?: Record<string, unknown>
  pwm?: Record<string, unknown>
  deadTime?: Record<string, unknown>
  plant?: Record<string, unknown>
  mapGrid?: Record<string, unknown>
  mapMode?: DriveMode
  nSamples?: number
  projectId?: string
}

export interface JobCreate {
  projectId: string
  jobType: JobType
  /** jobType=fem → FemJobPayload；jobType=drive → DriveJobPayload */
  payload?: FemJobPayload | DriveJobPayload | Record<string, unknown>
}

/** OpenAPI Job — 不含 payload */
export interface Job {
  id: string
  projectId: string
  jobType: JobType
  status: JobStatus
  /** fem 成功多为 solver/fem/jobs/{jobId}/manifest.json；drive → drive://jobs/{jobId} */
  resultRef?: string | null
  error?: ApiErrorBody | null
  createdAt: string
  updatedAt?: string
  /** drive/analytic may embed input+result for FE poll */
  payload?: Record<string, unknown> | null
}

export const JOB_TERMINAL_STATUSES: readonly JobStatus[] = [
  'succeeded',
  'failed',
  'cancelled',
] as const

export function isJobTerminal(status: JobStatus): boolean {
  return (JOB_TERMINAL_STATUSES as readonly string[]).includes(status)
}
