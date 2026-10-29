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

export interface UemExcitationState {
  operatingPoint: OperatingPoint
  /** 可选驱动草稿。不在本步提交 Jobs。 */
  driveDraft?: { mode?: string }
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
      barMaterialId: 'mat.acim.bar.aluminum-default',
      endRingMaterialId: 'mat.acim.endring.aluminum-default',
      cagePolePairs: 2,
    }
    return params
  }
  if (machineType === 'BLDC') return radialBase('BLDC', 12, 10)
  return radialBase('PMSM', 18, 6)
}

export function defaultMaterials(machineType: MachineType): UemMaterialsState {
  if (machineType === 'ACIM') {
    return {
      regions: {
        steel: 'mat-steel-m19',
        conductor: 'mat-copper',
        bar: 'mat-al-bar',
        endRing: 'mat.acim.endring.aluminum-default',
      },
      inline: { sigma_copper: 5.8e7, sigma_bar: 3.5e7 },
    }
  }
  return {
    regions: {
      steel: 'demo-steel',
      magnet: 'demo-N35',
      conductor: 'Cu',
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
