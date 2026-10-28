/**
 * FEM 精简结果可视化类型（Q3-6）。
 * 对齐 docs/drafts/Q3-轴向与FEM边界.md §5 与
 * packages/solver-fem/api/fem-manifest.schema.json。
 *
 * 浏览器默认只吃：
 * - role=scalars → JSON
 * - role=surface|slice → glTF / GLB
 * - role=preview → PNG（可选）
 * 禁止默认 VTK / 全场；勿再依赖旧 fem-result-v0 float32 grid 假彩主路径。
 */

/**
 * public dry-run。`/field` 仅在下列情况使用（见 FieldVizView.vue）：
 * 无 jobId；或 `?source=fixture`；或 artifacts 列表空/失败且关键 GET 404/不可达。
 */
export const FEM_MANIFEST_FIXTURE_BASE = '/fem/rf_pmsm_2d_dryrun' as const

export type FemJobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'
export type FemSolverKernel = 'elmer' | 'getdp'
export type FemDim = '2d' | '3d'
export type FemArtifactRole = 'scalars' | 'surface' | 'slice' | 'preview' | 'other'
export type FemArtifactFormat = 'json' | 'gltf' | 'glb' | 'png' | 'webp' | 'other'

export type FemArtifact = {
  /**
   * 相对 .mems 根的路径。
   * job-artifacts：GET /jobs/{jobId}/artifacts/{path}（按段编码，保留 `/`）。
   * fixture 降级：basename 映射到 public 目录。
   */
  path: string
  role: FemArtifactRole
  format: FemArtifactFormat
  bytes?: number
}

/** solver/fem/jobs/{jobId}/manifest.json */
export type FemManifest = {
  jobId: string
  status: FemJobStatus
  solverKernel: FemSolverKernel
  topology: 'RF' | 'AF'
  machineType: 'BLDC' | 'PMSM' | 'ACIM'
  dim: FemDim
  /** 关键标量摘要（列表 UI / 对照） */
  scalars: Record<string, unknown>
  artifacts: FemArtifact[]
  createdAt?: string
  updatedAt?: string
  /** FE mock 扩展；生产 manifest 可不含 */
  mock?: boolean
  note?: string
}

/** role=scalars 产物 JSON（可含比 manifest.scalars 更完整的块） */
export type FemScalarsArtifact = {
  torque_nm?: number
  back_emf_v_peak?: number
  losses_w?: Record<string, number>
  note?: string
  [key: string]: unknown
}
