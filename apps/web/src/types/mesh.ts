/** Mesh descriptor schema from packages/geometry (schemaVersion 0.1.0-q1). */

export const MESH_SCHEMA_VERSION = '0.1.0-q1' as const

export type MeshKind = 'radial' | 'axial'

export type MeshUnits = {
  length: 'mm' | 'm'
  angle: 'deg' | 'rad'
}

export type RingPrimitive = {
  type: 'ring'
  name: string
  innerRadius: number
  outerRadius: number
  height: number
  z: number
  radialSegments: number
  thetaSegments: number
}

export type SectorPrimitive = {
  type: 'sector'
  name: string
  innerRadius: number
  outerRadius: number
  height: number
  startAngleDeg: number
  sweepAngleDeg: number
  z: number
  segments: number
}

export type MeshPrimitive = RingPrimitive | SectorPrimitive

export type MeshMeta = {
  machineType?: string
  rotorTopology?: string
  config?: string
  slotCount?: number
  poleCount?: number
  diskCount?: number
  airgap?: number
  note?: string
  [key: string]: unknown
}

export type MeshDescriptor = {
  schemaVersion: string
  kind: MeshKind
  units: MeshUnits
  meta: MeshMeta
  primitives: MeshPrimitive[]
}
