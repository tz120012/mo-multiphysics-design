import type { MeshDescriptor, MeshHudDims, MeshPrimitive } from '@/types/mesh'

/** 从描述符抽出视口可观察量，便于核对槽/极/磁钢厚/盘厚是否进了 mesh。 */
export interface DescriptorSignals {
  primitives: number
  kind: string
  slotCount: number | null
  poleCount: number | null
  diskCount: number | null
  magnetCount: number
  /** 磁钢扇区径向厚度（mm，outer-inner 的最大值）。 */
  magnetBandMm: number | null
  /** 环图元高度最大值（轴向盘厚会反映在这里）。 */
  maxRingHeightMm: number | null
  toothOrSlotMarks: number
}

function num(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function primRole(prim: MeshPrimitive): string {
  return typeof prim.role === 'string' ? prim.role : ''
}

export function descriptorSignals(descriptor: MeshDescriptor | null): DescriptorSignals | null {
  if (!descriptor) return null
  let magnetCount = 0
  let magnetBand = 0
  let maxRingHeight = 0
  let toothOrSlotMarks = 0
  for (const prim of descriptor.primitives) {
    const role = primRole(prim)
    const magnetLike =
      role === 'magnet' || role === 'magnet_sector' || prim.name.startsWith('magnet')
    if (prim.type === 'sector' && magnetLike) {
      magnetCount += 1
      magnetBand = Math.max(magnetBand, prim.outerRadius - prim.innerRadius)
    }
    if (
      prim.type === 'sector' &&
      (role === 'stator_tooth' ||
        role === 'stator_slot' ||
        role === 'stator_slot_mark' ||
        prim.name.startsWith('stator_tooth') ||
        prim.name.startsWith('stator_slot'))
    ) {
      toothOrSlotMarks += 1
    }
    if (prim.type === 'ring') maxRingHeight = Math.max(maxRingHeight, prim.height)
  }
  return {
    primitives: descriptor.primitives.length,
    kind: descriptor.kind,
    slotCount: num(descriptor.meta.slotCount),
    poleCount: num(descriptor.meta.poleCount),
    diskCount: num(descriptor.meta.diskCount),
    magnetCount,
    magnetBandMm: magnetCount ? magnetBand : null,
    maxRingHeightMm: maxRingHeight ? maxRingHeight : null,
    toothOrSlotMarks,
  }
}

export interface ViewportHud {
  slotCount: number | null
  poleCount: number | null
  airgapMm: number | null
  magnetThicknessMm: number | null
  diskThicknessMm: number | null
  /** true 表示数值来自 meta.hudDims，而不是 meta 顶层旧键。 */
  fromHudDims: boolean
  source: string | null
  fidelity: string | null
  modelingComplete: boolean | null
  slotCavities: number
  airgapBands: number
}

function hudNum(dims: MeshHudDims | undefined, key: keyof MeshHudDims): number | null {
  if (!dims) return null
  return num(dims[key])
}

/** HUD 优先 hudDims；缺键再读 meta 顶层。三维刷新仍只看 meshDescriptor 图元。 */
export function viewportHud(descriptor: MeshDescriptor | null): ViewportHud | null {
  if (!descriptor) return null
  const meta = descriptor.meta
  const dims = meta.hudDims
  const fromHudDims = !!dims && typeof dims === 'object'
  let slotCavities = 0
  let airgapBands = 0
  for (const prim of descriptor.primitives) {
    const role = primRole(prim)
    if (role === 'stator_slot' || role === 'stator_slot_mark') slotCavities += 1
    if (role === 'airgap_band') airgapBands += 1
  }
  return {
    slotCount: hudNum(dims, 'slotCount') ?? num(meta.slotCount),
    poleCount: hudNum(dims, 'poleCount') ?? num(meta.poleCount),
    airgapMm: hudNum(dims, 'airgapMm') ?? num(meta.airgap),
    magnetThicknessMm: hudNum(dims, 'magnetThicknessMm') ?? num(meta.magnetThickness),
    diskThicknessMm: hudNum(dims, 'diskThicknessMm') ?? num(meta.diskThickness),
    fromHudDims,
    source: typeof meta.source === 'string' ? meta.source : null,
    fidelity: typeof meta.fidelity === 'string' ? meta.fidelity : null,
    modelingComplete: typeof meta.modelingComplete === 'boolean' ? meta.modelingComplete : null,
    slotCavities,
    airgapBands,
  }
}
