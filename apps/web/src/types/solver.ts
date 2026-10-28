/**
 * Mo solver-analytic Solve API v0 — 手写对齐
 * packages/solver-analytic/api/solve.schema.json (schema_version: 0.0.0-gate0)
 */

export const SOLVE_SCHEMA_VERSION = '0.0.0-gate0' as const
export type SolveSchemaVersion = typeof SOLVE_SCHEMA_VERSION

export type Topology = 'RF' | 'AF'
export type MachineType = 'BLDC' | 'PMSM' | 'ACIM'
export type SolverKind = 'mec' | 'axial_planes' | 'mock'

export interface GeometrySummary {
  poles: number
  slots: number
  stack_length_m: number
  airgap_m: number
  rotor_od_m: number
  stator_id_m: number
  magnet_thickness_m?: number
  turns_per_phase?: number
}

export interface Materials {
  steel_id?: string
  magnet_id?: string
  conductor_id?: string
  /** Remanence override for mock/PM machines */
  br_t?: number
  /** S/m, optional */
  sigma_copper?: number
}

export interface OperatingPoint {
  speed_rpm: number
  current_a_peak?: number
  voltage_v_peak?: number
  /** Current angle, PMSM */
  gamma_deg?: number
  /** ACIM only */
  slip?: number
}

export interface SolveRequest {
  schema_version: SolveSchemaVersion
  topology: Topology
  machine_type: MachineType
  geometry: GeometrySummary
  materials: Materials
  operating_point: OperatingPoint
}

export interface SolveMeta {
  solver: SolverKind
  elapsed_ms: number
  mock: boolean
  note?: string
  /** MEC diagnostics (optional, present on fixture) */
  mec?: Record<string, unknown>
}

export interface LossesW {
  copper: number
  iron: number
  magnet_eddy?: number
  /** ACIM */
  rotor_bar?: number
}

export interface InductanceH {
  ld?: number
  lq?: number
}

export interface SolveResult {
  schema_version: SolveSchemaVersion
  meta: SolveMeta
  torque_nm: number
  back_emf_v_peak: number
  losses_w: LossesW
  inductance_h?: InductanceH
}

/** 转速扫描曲线点（多次改 operating_point 拼点） */
export interface SweepPoint {
  speed_rpm: number
  torque_nm: number
  back_emf_v_peak: number
  slip?: number
}

/** 径向 PMSM 样例请求（与 api/examples/radial_pmsm_request.json 一致） */
export const DEFAULT_RADIAL_PMSM_REQUEST: SolveRequest = {
  schema_version: SOLVE_SCHEMA_VERSION,
  topology: 'RF',
  machine_type: 'PMSM',
  geometry: {
    poles: 10,
    slots: 12,
    stack_length_m: 0.04,
    airgap_m: 0.0008,
    rotor_od_m: 0.06,
    stator_id_m: 0.0616,
    magnet_thickness_m: 0.003,
    turns_per_phase: 48,
  },
  materials: {
    steel_id: 'demo-steel',
    magnet_id: 'demo-N35',
    conductor_id: 'Cu',
    br_t: 1.2,
  },
  operating_point: {
    speed_rpm: 3000,
    current_a_peak: 25,
    gamma_deg: 0,
  },
}
