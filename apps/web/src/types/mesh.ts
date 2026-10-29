/** Mesh descriptor schema from packages/geometry (schemaVersion 0.1.0-q1). */

export const MESH_SCHEMA_VERSION = '0.1.0-q1' as const

export type MeshKind = 'radial' | 'axial'

export type MeshUnits = {
  length: 'mm' | 'm'
  angle: 'deg' | 'rad'
}

/** Q7-4 可选。缺省时 FE 按 name 前缀上色。 */
export type MeshPrimitiveRole =
  | 'stator_yoke'
  | 'stator_tooth'
  | 'stator_slot'
  | 'rotor_core'
  | 'airgap_band'
  | 'magnet'
  | 'acim_bar'
  | 'stator_disk'
  | 'rotor_disk'
  | 'stator_slot_mark'
  | 'magnet_sector'
  | (string & {})

export type RingPrimitive = {
  type: 'ring'
  name: string
  role?: MeshPrimitiveRole
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
  role?: MeshPrimitiveRole
  innerRadius: number
  outerRadius: number
  height: number
  startAngleDeg: number
  sweepAngleDeg: number
  z: number
  segments: number
}

export type MeshPrimitive = RingPrimitive | SectorPrimitive

/** FE HUD 稳定键。缺键则省略，不发明数值。 */
export type MeshHudDims = {
  slotCount?: number
  poleCount?: number
  airgapMm?: number
  magnetThicknessMm?: number
  diskThicknessMm?: number
}

export type MeshMeta = {
  machineType?: string
  rotorTopology?: string
  config?: string
  slotCount?: number
  poleCount?: number
  diskCount?: number
  airgap?: number
  magnetThickness?: number
  diskThickness?: number
  note?: string
  /** parametric-rebuild。旧描述符可缺。 */
  source?: string
  /** 几何侧硬钉 false。FE 不得据此宣称建模完成。 */
  modelingComplete?: boolean
  /** constructive-descriptor。旧描述符可缺。 */
  fidelity?: string
  hudDims?: MeshHudDims
  [key: string]: unknown
}

export type MeshDescriptor = {
  schemaVersion: string
  kind: MeshKind
  units: MeshUnits
  meta: MeshMeta
  primitives: MeshPrimitive[]
}
