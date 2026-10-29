import type { MeshDescriptor } from '@/types/mesh'

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

export function descriptorSignals(descriptor: MeshDescriptor | null): DescriptorSignals | null {
  if (!descriptor) return null
  let magnetCount = 0
  let magnetBand = 0
  let maxRingHeight = 0
  let toothOrSlotMarks = 0
  for (const prim of descriptor.primitives) {
    if (prim.type === 'sector' && prim.name.startsWith('magnet')) {
      magnetCount += 1
      magnetBand = Math.max(magnetBand, prim.outerRadius - prim.innerRadius)
    }
    if (
      prim.type === 'sector' &&
      (prim.name.startsWith('stator_tooth') || prim.name.startsWith('stator_slot'))
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
