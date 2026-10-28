/**
 * 轴向 AF-PMSM 全流程入口类型（对齐 Mo-几何 tip 1bd8b51）。
 * 权威样例：public/geometry/axial_af_pmsm_rfmr_pipeline_entry.json
 * （源自 packages/geometry/examples/…；packages tip 硬接后勿再本地发明字段）。
 *
 * 钉死：
 * - poles = poleCount（极数；UI 极对数 = poleCount/2 只展示）
 * - AF stack_length_m = diskThickness/1000（length=mm → SI 米；不乘 diskCount）
 * - analyticSolveStub.schema_version = 0.0.0-gate0（材料/工况由 FE 填）
 * - femEntryHint.schemaVersion = 0.1.0-q3-hint（无网格）
 */
import type { GeometrySummary, Materials, OperatingPoint, SolveSchemaVersion } from '@/types/solver'
import type { MeshDescriptor } from '@/types/mesh'

export type { GeometrySummary }

export const FEM_ENTRY_HINT_SCHEMA_VERSION = '0.1.0-q3-hint' as const

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
 * 本地从 AF params 拼最小 GeometrySummary（mm→m）。
 * 等 packages/geometry tip 硬接后优先用 entry.geometrySummary。
 */
export function summarizeAxialPmsmLocal(params: AxialGeometryParams): GeometrySummary {
  const lu = params.units?.length ?? 'mm'
  const toM = (v: number) => (lu === 'm' ? v : v / 1000)
  const p = params.pmsm
  const summary: GeometrySummary = {
    poles: p.poleCount,
    slots: p.slotCount,
    stack_length_m: toM(p.diskThickness),
    airgap_m: toM(p.airgap),
    rotor_od_m: toM(p.outerDiameter),
    stator_id_m: toM(p.innerDiameter),
  }
  if (p.magnetThickness != null) {
    summary.magnet_thickness_m = toM(p.magnetThickness)
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
