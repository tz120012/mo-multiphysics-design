/**
 * Q7-1：区域只绑定材料目录种子 id。
 * 目录 GET 失败时仍用这份清单，不回退 demo-steel / demo-N35 / 裸 Cu。
 */
import type { UemMaterialRegions } from '@/lib/geometryDefaults'
import type { Material } from '@/types/materials'

export const SEED_MATERIAL_IDS = [
  'mat-steel-m19',
  'mat-steel-50ww470',
  'mat-ndfeb-n42',
  'mat-ndfeb-n35',
  'mat-copper',
  'mat-coil-al',
  'mat-acim-bar-al',
  'mat-acim-bar-cu',
  'mat-acim-endring-al',
] as const

export type SeedMaterialId = (typeof SEED_MATERIAL_IDS)[number]

export const SEED_BY_REGION: Record<keyof UemMaterialRegions, readonly SeedMaterialId[]> = {
  steel: ['mat-steel-m19', 'mat-steel-50ww470'],
  magnet: ['mat-ndfeb-n42', 'mat-ndfeb-n35'],
  conductor: ['mat-copper', 'mat-coil-al'],
  bar: ['mat-acim-bar-al', 'mat-acim-bar-cu'],
  endRing: ['mat-acim-endring-al'],
}

export interface CatalogOption {
  id: SeedMaterialId
  name: string
  label: string
}

export function isSeedMaterialId(id: string): id is SeedMaterialId {
  return (SEED_MATERIAL_IDS as readonly string[]).includes(id)
}

export function optionsForRegion(
  region: keyof UemMaterialRegions,
  items: Material[] | null,
): CatalogOption[] {
  return SEED_BY_REGION[region].map((id) => {
    const hit = items?.find((item) => item.id === id)
    const name = hit?.name?.trim() || id
    return {
      id,
      name,
      label: hit?.name ? `${hit.name} · ${id}` : id,
    }
  })
}

export function catalogName(id: string, items: Material[] | null): string {
  const hit = items?.find((item) => item.id === id)
  return hit?.name?.trim() || ''
}
