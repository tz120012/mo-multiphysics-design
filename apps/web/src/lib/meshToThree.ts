import * as THREE from 'three'
import type {
  MeshDescriptor,
  MeshPrimitive,
  MeshPrimitiveRole,
  RingPrimitive,
  SectorPrimitive,
} from '@/types/mesh'

/** mm → scene units (meters). Geometry package emits length in mm. */
export const MM_TO_SCENE = 0.001

const COLOR_BY_PREFIX: { test: (name: string) => boolean; color: number }[] = [
  { test: (n) => n.startsWith('stator'), color: 0x2dd4bf },
  { test: (n) => n.startsWith('rotor'), color: 0x64748b },
  { test: (n) => n.startsWith('magnet'), color: 0xf59e0b },
  { test: (n) => n.startsWith('acim'), color: 0xd97706 },
]

export function colorForPrimitiveName(name: string): number {
  for (const entry of COLOR_BY_PREFIX) {
    if (entry.test(name)) return entry.color
  }
  return 0x94a3b8
}

const STYLE_BY_ROLE: Partial<Record<MeshPrimitiveRole, { color: number; opacity: number }>> = {
  stator_yoke: { color: 0x14b8a6, opacity: 1 },
  stator_tooth: { color: 0x22d3ee, opacity: 1 },
  stator_slot: { color: 0x1e293b, opacity: 0.42 },
  rotor_core: { color: 0x64748b, opacity: 1 },
  airgap_band: { color: 0x38bdf8, opacity: 0.32 },
  magnet: { color: 0xf59e0b, opacity: 1 },
  acim_bar: { color: 0xea580c, opacity: 1 },
  stator_disk: { color: 0x2dd4bf, opacity: 1 },
  rotor_disk: { color: 0x94a3b8, opacity: 1 },
  stator_slot_mark: { color: 0x67e8f9, opacity: 0.58 },
  magnet_sector: { color: 0xfbbf24, opacity: 1 },
}

/** role 优先；没有 role 时退回 name 前缀。槽腔 / 气隙环用半透明，避免整圈实心样例感。 */
export function styleForPrimitive(prim: { name: string; role?: string }): {
  color: number
  opacity: number
} {
  if (prim.role && STYLE_BY_ROLE[prim.role]) {
    return STYLE_BY_ROLE[prim.role] as { color: number; opacity: number }
  }
  return { color: colorForPrimitiveName(prim.name), opacity: 1 }
}

function scaleLen(mm: number, unitsLength: string): number {
  const mmValue = unitsLength === 'm' ? mm * 1000 : mm
  return mmValue * MM_TO_SCENE
}

function buildRingGeometry(p: RingPrimitive, unitsLength: string): THREE.BufferGeometry {
  const inner = scaleLen(p.innerRadius, unitsLength)
  const outer = scaleLen(p.outerRadius, unitsLength)
  const height = Math.max(scaleLen(p.height, unitsLength), 1e-6)
  const segments = Math.max(8, p.thetaSegments || p.radialSegments || 32)

  const shape = new THREE.Shape()
  shape.absarc(0, 0, outer, 0, Math.PI * 2, false)
  const hole = new THREE.Path()
  hole.absarc(0, 0, Math.max(inner, 1e-6), 0, Math.PI * 2, true)
  shape.holes.push(hole)

  const geo = new THREE.ExtrudeGeometry(shape, {
    depth: height,
    bevelEnabled: false,
    curveSegments: segments,
  })
  // Center extrusion on z, then offset by primitive z
  geo.translate(0, 0, -height / 2)
  return geo
}

function buildSectorGeometry(p: SectorPrimitive, unitsLength: string): THREE.BufferGeometry {
  const inner = scaleLen(p.innerRadius, unitsLength)
  const outer = scaleLen(p.outerRadius, unitsLength)
  const height = Math.max(scaleLen(p.height, unitsLength), 1e-6)
  const segments = Math.max(4, p.segments || 8)
  const start = THREE.MathUtils.degToRad(p.startAngleDeg)
  const end = start + THREE.MathUtils.degToRad(p.sweepAngleDeg)

  const shape = new THREE.Shape()
  shape.absarc(0, 0, outer, start, end, false)
  shape.absarc(0, 0, Math.max(inner, 1e-6), end, start, true)

  const geo = new THREE.ExtrudeGeometry(shape, {
    depth: height,
    bevelEnabled: false,
    curveSegments: segments,
  })
  geo.translate(0, 0, -height / 2)
  return geo
}

function geometryFromPrimitive(
  p: MeshPrimitive,
  unitsLength: string,
): THREE.BufferGeometry {
  if (p.type === 'ring') return buildRingGeometry(p, unitsLength)
  if (p.type === 'sector') return buildSectorGeometry(p, unitsLength)
  const _exhaustive: never = p
  void _exhaustive
  return new THREE.BufferGeometry()
}

/** Build a Three.js Group of Meshes from a mesh descriptor. Caller owns disposal. */
export function meshDescriptorToGroup(descriptor: MeshDescriptor): THREE.Group {
  const group = new THREE.Group()
  group.name = `mesh_${descriptor.kind}`
  const unitsLength = descriptor.units?.length ?? 'mm'

  for (const prim of descriptor.primitives) {
    const geometry = geometryFromPrimitive(prim, unitsLength)
    const style = styleForPrimitive(prim)
    const material = new THREE.MeshStandardMaterial({
      color: style.color,
      metalness: style.opacity < 1 ? 0.05 : 0.35,
      roughness: style.opacity < 1 ? 0.85 : 0.55,
      side: THREE.DoubleSide,
      transparent: style.opacity < 1,
      opacity: style.opacity,
      depthWrite: style.opacity >= 1,
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.name = prim.name
    mesh.renderOrder = style.opacity < 1 ? 2 : 0
    const z = scaleLen(prim.z ?? 0, unitsLength)
    mesh.position.z = z
    group.add(mesh)
  }

  return group
}

/** Dispose geometries and materials of a group previously created by meshDescriptorToGroup. */
export function disposeObject3D(root: THREE.Object3D): void {
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh
    if (mesh.isMesh) {
      mesh.geometry?.dispose()
      const mat = mesh.material
      if (Array.isArray(mat)) mat.forEach((m) => m.dispose())
      else mat?.dispose()
    }
  })
}
