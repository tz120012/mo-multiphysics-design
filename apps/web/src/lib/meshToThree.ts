import * as THREE from 'three'
import type {
  MeshDescriptor,
  MeshPrimitive,
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
    const material = new THREE.MeshStandardMaterial({
      color: colorForPrimitiveName(prim.name),
      metalness: 0.35,
      roughness: 0.55,
      side: THREE.DoubleSide,
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.name = prim.name
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
