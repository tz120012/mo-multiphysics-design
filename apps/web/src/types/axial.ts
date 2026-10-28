/**
 * 轴向 AF-PMSM 全流程入口类型（对齐 Mo-几何 tip ad66ff9）。
 * 权威样例：public/geometry/axial_af_pmsm_rfmr_pipeline_entry.json
 * （源自 packages/geometry/examples/…；勿再本地发明字段）。
 *
 * 钉死：
 * - poles = poleCount（极数；UI 极对数 = poleCount/2 只展示）
 * - AF stack_length_m = disk_thickness_m = diskThickness → m（不乘 diskCount）
 * - outer_radius_m = outerDiameter/2，inner_radius_m = innerDiameter/2
 * - disk_count = diskCount；n_planes 默认 4；可选 magnet_arc_ratio = magnetSectorAngle/180
 * - analyticSolveStub.schema_version = 0.0.0-gate0（材料/工况由 FE 填）
 * - femEntryHint.schemaVersion = 0.1.0-q3-hint（无网格）
 */
import type { GeometrySummary, Materials, OperatingPoint, SolveSchemaVersion } from '@/types/solver'
import type { MeshDescriptor } from '@/types/mesh'

export type { GeometrySummary }

export const FEM_ENTRY_HINT_SCHEMA_VERSION = '0.1.0-q3-hint' as const

/** 与 mo_geometry.constants.DEFAULT_N_PLANES / axial_planes 对齐 */
export const AF_DEFAULT_N_PLANES = 4

export type AxialPmsmParams = {
  innerDiameter: number
  outerDiameter: number
  diskCount: number
  airgap: number
  diskThickness: number
  magnetSectorAngle: number
  slotCount: number
  poleCount: number
  magnetThickness?: number
}

/** geometry/params 片段（AF-PMSM） */
export type AxialGeometryParams = {
  schemaVersion: string
  topology: 'AF'
  machineType: 'PMSM'
  config: 'RFMR' | 'FRMF' | string
  units: { length: 'mm' | 'm'; angle: 'deg' | 'rad' }
  pmsm: AxialPmsmParams
}

export type FemEntryHint = {
  schemaVersion: typeof FEM_ENTRY_HINT_SCHEMA_VERSION | string
  topology: 'AF'
  machineType: 'PMSM'
  config?: string
  units: { length: 'mm' | 'm'; angle: 'deg' | 'rad' }
  innerDiameter: number
  outerDiameter: number
  diskCount: number
  airgap: number
  diskThickness: number
  slotCount: number
  poleCount: number
  note?: string
}

export type AnalyticSolveStub = {
  schema_version: SolveSchemaVersion | string
  topology: 'AF'
  machine_type: 'PMSM'
  geometry: GeometrySummary
  materials: Materials
  operating_point: OperatingPoint
}

/** Mo-几何 export_axial_pipeline_entry 返回形状 */
export type AxialPipelineEntry = {
  geometryParams: AxialGeometryParams
  geometrySummary: GeometrySummary
  meshDescriptor: MeshDescriptor
  analyticSolveStub: AnalyticSolveStub
  femEntryHint: FemEntryHint
}

/**
 * 本地从 AF params 拼 GeometrySummary（mm→m）。
 * 字段与 packages/geometry export_geometry_summary(AF) / 静态 snapshot 对齐。
 * 浏览器调参仍走本地重算；不调用 rebuild_live_geometry。
 */
export function summarizeAxialPmsmLocal(params: AxialGeometryParams): GeometrySummary {
  const lu = params.units?.length ?? 'mm'
  const toM = (v: number) => (lu === 'm' ? v : v / 1000)
  const p = params.pmsm
  const rotorOd = toM(p.outerDiameter)
  const statorId = toM(p.innerDiameter)
  const diskThickness = toM(p.diskThickness)
  const summary: GeometrySummary = {
    poles: p.poleCount,
    slots: p.slotCount,
    stack_length_m: diskThickness,
    airgap_m: toM(p.airgap),
    rotor_od_m: rotorOd,
    stator_id_m: statorId,
    outer_radius_m: rotorOd / 2,
    inner_radius_m: statorId / 2,
    disk_thickness_m: diskThickness,
    disk_count: p.diskCount,
    n_planes: AF_DEFAULT_N_PLANES,
  }
  if (p.magnetThickness != null) {
    summary.magnet_thickness_m = toM(p.magnetThickness)
  }
  // magnetSectorAngle 单位为 deg、(0, 180]；ratio = angle/180 ∈ (0, 1]
  const ratio = p.magnetSectorAngle / 180
  if (ratio > 0 && ratio <= 1) {
    summary.magnet_arc_ratio = ratio
  }
  return summary
}

/** 本地最小 femEntryHint（无网格） */
export function buildFemEntryHintLocal(params: AxialGeometryParams): FemEntryHint {
  const lu = params.units?.length ?? 'mm'
  const toMm = (v: number) => (lu === 'mm' ? v : v * 1000)
  const p = params.pmsm
  return {
    schemaVersion: FEM_ENTRY_HINT_SCHEMA_VERSION,
    topology: 'AF',
    machineType: 'PMSM',
    config: params.config,
    units: { length: 'mm', angle: params.units?.angle ?? 'deg' },
    innerDiameter: toMm(p.innerDiameter),
    outerDiameter: toMm(p.outerDiameter),
    diskCount: p.diskCount,
    airgap: toMm(p.airgap),
    diskThickness: toMm(p.diskThickness),
    slotCount: p.slotCount,
    poleCount: p.poleCount,
    note: 'Q3 FE-local hint; replace when packages/geometry export is wired live',
  }
}
