import type { MachineType, Topology } from '@/api/types'
import type { Materials, OperatingPoint } from '@/types/solver'

/** geometry/params.json schema（与 packages/geometry 一致；≠ mems 整包版本）。 */
export const GEOMETRY_PARAMS_SCHEMA = '0.1.0-q1' as const

export interface GeometryParams {
  schemaVersion: string
  topology: Topology
  machineType: MachineType
  units: { length: string; angle: string }
  rotorTopology?: string
  stator?: Record<string, unknown>
  rotor?: Record<string, unknown>
  airgap?: number
  axialActiveLength?: number
  acim?: Record<string, unknown>
  config?: string
  pmsm?: Record<string, unknown>
  [key: string]: unknown
}

export interface SessionMachineOption {
  key: string
  label: string
  topology: Topology
  machineType: MachineType
}

/** P0 有描述符的机型。AF 非 PMSM 不在此列表。 */
export const SESSION_MACHINES: SessionMachineOption[] = [
  { key: 'RF:PMSM', label: 'RF-PMSM', topology: 'RF', machineType: 'PMSM' },
  { key: 'RF:BLDC', label: 'RF-BLDC', topology: 'RF', machineType: 'BLDC' },
  { key: 'RF:ACIM', label: 'RF-ACIM', topology: 'RF', machineType: 'ACIM' },
  { key: 'AF:PMSM', label: 'AF-PMSM', topology: 'AF', machineType: 'PMSM' },
]

export function machineKey(topology: Topology, machineType: MachineType): string {
  if (topology === 'AF') return 'AF:PMSM'
  return `RF:${machineType}`
}

export interface UemMaterialRegions {
  steel?: string
  magnet?: string
  conductor?: string
  bar?: string
  endRing?: string
}

export interface UemMaterialsState {
  /** 区域 → materialId。P0 占位，不是完整材料库。 */
  regions: UemMaterialRegions
  inline: Pick<Materials, 'br_t' | 'mur_pm' | 'sigma_copper' | 'sigma_bar'>
}

/** 可选驱动草稿（Q7-2）。写入 UEM；预览复用 Jobs jobType=drive。 */
export interface UemDriveDraft {
  mode?: 'bldc_square' | 'pmsm_foc' | 'acim_vf' | 'acim_foc' | string
  pwm?: { carrierHz?: number; modIndex?: number; scheme?: 'svpwm' | 'spwm' }
  deadTime?: { tdeadUs?: number }
  /** 可选：驱动工况覆盖（优先于 operatingPoint 启发） */
  iqA?: number
  idA?: number
  torqueNm?: number
  tempC?: number
  slip?: number
}

export interface UemExcitationState {
  operatingPoint: OperatingPoint
  /** 可选驱动草稿。本步可不强制跑 Jobs；预览走既有 drive Job。 */
  driveDraft?: UemDriveDraft
}

function mmUnits(): { length: string; angle: string } {
  return { length: 'mm', angle: 'deg' }
}

function radialBase(machineType: MachineType, slotCount: number, poleCount: number): GeometryParams {
  return {
    schemaVersion: GEOMETRY_PARAMS_SCHEMA,
    topology: 'RF',
    machineType,
    units: mmUnits(),
    rotorTopology: 'inner',
    stator: {
      innerDiameter: 51,
      outerDiameter: 80,
      stackLength: 25,
      slotCount,
      slotShape: 'straight',
      toothWidth: 4.5,
      yokeHeight: 5,
      skewAngle: null,
    },
    rotor: {
      innerDiameter: 15,
      outerDiameter: 50,
      magnetTopology: 'SPM',
      poleCount,
      magnetThickness: 3,
    },
    airgap: 0.5,
    axialActiveLength: 25,
  }
}

/** 与 public/mesh 样例及 geometry 默认量级对齐的会话初值（mm, camel）。 */
export function defaultGeometryParams(topology: Topology, machineType: MachineType): GeometryParams {
  if (topology === 'AF') {
    return {
      schemaVersion: GEOMETRY_PARAMS_SCHEMA,
      topology: 'AF',
      machineType: 'PMSM',
      config: 'RFMR',
      units: mmUnits(),
      pmsm: {
        innerDiameter: 40,
        outerDiameter: 120,
        diskCount: 3,
        airgap: 1,
        diskThickness: 8,
        magnetThickness: 2,
        magnetSectorAngle: 150,
        slotCount: 12,
        poleCount: 10,
      },
    }
  }
  if (machineType === 'ACIM') {
    const params = radialBase('ACIM', 36, 4)
    params.acim = {
      barSlotShape: 'rectangular',
      barCrossSection: { width: 4, height: 12 },
      endRingSection: { width: 8, height: 10 },
      barMaterialId: 'mat-acim-bar-al',
      endRingMaterialId: 'mat-acim-endring-al',
      cagePolePairs: 2,
    }
    return params
  }
  if (machineType === 'BLDC') return radialBase('BLDC', 12, 10)
  return radialBase('PMSM', 18, 6)
}

/**
 * 材料服务种子没有这些旧别名。求解前改写成目录 id，避免 GET /materials/{id} 404。
 * 只含 Motor 确认的映射，不另造 id。
 */
const LEGACY_MATERIAL_IDS: Record<string, string> = {
  'demo-steel': 'mat-steel-m19',
  'demo-N35': 'mat-ndfeb-n35',
  Cu: 'mat-copper',
  'mat-al-bar': 'mat-acim-bar-al',
}

export function catalogMaterialId(id: string | undefined): string | undefined {
  if (!id) return id
  return LEGACY_MATERIAL_IDS[id] ?? id
}

const REGION_KEYS = ['steel', 'magnet', 'conductor', 'bar', 'endRing'] as const

/** 把会话里残留的旧别名改成目录 id，便于材料表单和 GET 使用同一套种子。 */
export function alignMaterialRegions(regions: UemMaterialRegions): {
  regions: UemMaterialRegions
  rewritten: string[]
} {
  const next: UemMaterialRegions = { ...regions }
  const rewritten: string[] = []
  for (const key of REGION_KEYS) {
    const raw = next[key]
    const mapped = catalogMaterialId(raw)
    if (raw && mapped && mapped !== raw) {
      next[key] = mapped
      rewritten.push(`${raw} → ${mapped}`)
    }
  }
  return { regions: next, rewritten }
}

export function defaultMaterials(machineType: MachineType): UemMaterialsState {
  if (machineType === 'ACIM') {
    return {
      regions: {
        steel: 'mat-steel-m19',
        conductor: 'mat-copper',
        bar: 'mat-acim-bar-al',
        endRing: 'mat-acim-endring-al',
      },
      inline: { sigma_copper: 5.8e7, sigma_bar: 3.5e7 },
    }
  }
  return {
    regions: {
      steel: 'mat-steel-m19',
      magnet: 'mat-ndfeb-n35',
      conductor: 'mat-copper',
    },
    inline: { br_t: machineType === 'BLDC' ? 1.1 : 1.2 },
  }
}

export function defaultExcitation(topology: Topology, machineType: MachineType): UemExcitationState {
  if (machineType === 'ACIM') {
    return {
      operatingPoint: { speed_rpm: 1450, voltage_v_peak: 311, freq_hz: 50 },
      driveDraft: { mode: 'acim_vf' },
    }
  }
  if (topology === 'AF') {
    return {
      operatingPoint: { speed_rpm: 1500, current_a_peak: 10, gamma_deg: 0 },
      driveDraft: { mode: 'pmsm_foc' },
    }
  }
  if (machineType === 'BLDC') {
    return {
      operatingPoint: { speed_rpm: 3000, current_a_peak: 20 },
      driveDraft: { mode: 'bldc_square' },
    }
  }
  return {
    operatingPoint: { speed_rpm: 3000, current_a_peak: 25, gamma_deg: 0 },
    driveDraft: { mode: 'pmsm_foc' },
  }
}

export function isGeometryParams(value: unknown): value is GeometryParams {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  const topo = (value as { topology?: unknown }).topology
  return topo === 'RF' || topo === 'AF'
}

export function normalizeMachine(topology: Topology, machineType: MachineType): {
  topology: Topology
  machineType: MachineType
} {
  if (topology === 'AF') return { topology: 'AF', machineType: 'PMSM' }
  return { topology: 'RF', machineType }
}
