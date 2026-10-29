import type { Materials, OperatingPoint, SolveRequest } from '@/types/solver'
import { SOLVE_SCHEMA_VERSION } from '@/types/solver'

/**
 * FE 镜像 packages/solver-analytic/api/compose_request.py compose_solve_request。
 * 不发明几何：geometry 必须是已有 GeometrySummary（来自 rebuild）。
 */

const REQUIRED_GEOM = [
  'poles',
  'slots',
  'stack_length_m',
  'airgap_m',
  'rotor_od_m',
  'stator_id_m',
] as const

export function composeSolveRequest(input: {
  topology: string
  machineType: string
  geometry: Record<string, unknown>
  materials: Materials
  operatingPoint: OperatingPoint
}): SolveRequest {
  const geometry = input.geometry
  const materials = input.materials
  const operatingPoint = input.operatingPoint
  if (!geometry || typeof geometry !== 'object' || Array.isArray(geometry)) {
    throw new Error('geometry 必须是 GeometrySummary 对象')
  }
  if (!materials || typeof materials !== 'object') throw new Error('materials 必须是对象')
  if (!operatingPoint || typeof operatingPoint !== 'object') {
    throw new Error('operating_point 必须是对象')
  }

  const topology = input.topology.trim().toUpperCase()
  const machineType = input.machineType.trim().toUpperCase()
  if (topology !== 'RF' && topology !== 'AF') {
    throw new Error(`topology 须为 RF 或 AF，当前 ${input.topology}`)
  }
  if (machineType !== 'PMSM' && machineType !== 'BLDC' && machineType !== 'ACIM') {
    throw new Error(`machine_type 须为 PMSM、BLDC 或 ACIM，当前 ${input.machineType}`)
  }

  const missing = REQUIRED_GEOM.filter((key) => !(key in geometry))
  if (missing.length) throw new Error(`geometry 缺少字段：${missing.join(', ')}`)

  return {
    schema_version: SOLVE_SCHEMA_VERSION,
    topology,
    machine_type: machineType,
    geometry: structuredClone(geometry) as unknown as SolveRequest['geometry'],
    materials: structuredClone(materials),
    operating_point: structuredClone(operatingPoint),
  }
}
