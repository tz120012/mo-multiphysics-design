/**
 * Mo solver-analytic Solve API v0 — 手写对齐
 * packages/solver-analytic/api/solve.schema.json (schema_version: 0.0.0-gate0)
 * Q2 适配层降级序见 docs/drafts/Q2-材料与解析边界.md §3.3
 */

export const SOLVE_SCHEMA_VERSION = '0.0.0-gate0' as const
export type SolveSchemaVersion = typeof SOLVE_SCHEMA_VERSION

export type Topology = 'RF' | 'AF'
export type MachineType = 'BLDC' | 'PMSM' | 'ACIM'
/** 内核种类（真核 / 等效电路 / mock） */
export type SolverKind = 'mec' | 'axial_planes' | 'mock' | 'acim_equiv'
/**
 * FE 交互路径来源（local-first 降级序标注）。
 * Wasm → sync → fixture/mock；Jobs 不阻塞 UI。
 */
export type SolveBackend = 'wasm' | 'sync' | 'fixture' | 'mock'

export interface GeometrySummary {
  poles: number
  slots: number
  stack_length_m: number
  airgap_m: number
  rotor_od_m: number
  stator_id_m: number
  magnet_thickness_m?: number
  turns_per_phase?: number
  /** ACIM */
  rotor_bars?: number
  /** ACIM bar cross-section m² */
  bar_area_m2?: number
  winding_factor?: number
  carter_factor?: number
  /** AF multi-plane count */
  n_planes?: number
  disk_thickness_m?: number
}

export interface Materials {
  steel_id?: string
  magnet_id?: string
  conductor_id?: string
  /** ACIM rotor bar material id */
  bar_id?: string
  /** Remanence override for mock/PM machines */
  br_t?: number
  mur_pm?: number
  /** S/m, stator conductor */
  sigma_copper?: number
  /** S/m, ACIM bar */
  sigma_bar?: number
}

export interface OperatingPoint {
  speed_rpm: number
  current_a_peak?: number
  voltage_v_peak?: number
  /** Current angle, PMSM/BLDC */
  gamma_deg?: number
  /** ACIM only */
  slip?: number
  /** ACIM supply frequency; default 50 */
  freq_hz?: number
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
  /**
   * FE 适配层标注：本结果实际走了哪条路径。
   * 见 docs/drafts/Q2-材料与解析边界.md 降级序 Wasm→sync→fixture/mock。
   */
  source?: SolveBackend
  /** MEC diagnostics (optional, present on fixture) */
  mec?: Record<string, unknown>
  /** ACIM equivalent-circuit diagnostics */
  acim?: Record<string, unknown>
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

/** 径向 PMSM 样例请求（与 public/solver/radial_pmsm_request.json 一致） */
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
    steel_id: 'mat-steel-m19',
    magnet_id: 'mat-ndfeb-n35',
    conductor_id: 'mat-copper',
    br_t: 1.2,
  },
  operating_point: {
    speed_rpm: 3000,
    current_a_peak: 25,
    gamma_deg: 0,
  },
}

/** 径向 ACIM 样例（与 public/solver/radial_acim_request.json / Mo-解析 smoke 一致） */
export const DEFAULT_RADIAL_ACIM_REQUEST: SolveRequest = {
  schema_version: SOLVE_SCHEMA_VERSION,
  topology: 'RF',
  machine_type: 'ACIM',
  geometry: {
    poles: 4,
    slots: 36,
    stack_length_m: 0.12,
    airgap_m: 0.0005,
    rotor_od_m: 0.119,
    stator_id_m: 0.12,
    turns_per_phase: 96,
    rotor_bars: 28,
    bar_area_m2: 5.0e-5,
  },
  materials: {
    steel_id: 'mat-steel-m19',
    conductor_id: 'mat-copper',
    bar_id: 'mat-acim-bar-al',
    sigma_copper: 5.8e7,
    sigma_bar: 3.5e7,
  },
  operating_point: {
    speed_rpm: 1450,
    voltage_v_peak: 311.0,
    freq_hz: 50.0,
  },
}
