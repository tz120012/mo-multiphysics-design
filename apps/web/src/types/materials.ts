/**
 * Materials API 最小类型 — 对齐 docs/drafts/openapi-v1.yaml +
 * docs/drafts/Q2-材料与解析边界.md（materialsSchemaVersion: 0.1.0-q2）
 */

export const MATERIALS_SCHEMA_VERSION = '0.1.0-q2' as const
export type MaterialsSchemaVersion = typeof MATERIALS_SCHEMA_VERSION

export type MaterialCategory = 'steel' | 'magnet' | 'coil' | 'acim_bar'

export interface CurveTable2D {
  xName: string
  yName: string
  xUnit?: string
  yUnit?: string
  points: [number, number][]
  note?: string
}

export interface SteelProps {
  bh?: CurveTable2D
  bp?: CurveTable2D
  lossCoefficients?: Record<string, unknown>
}

export interface MagnetProps {
  br_t: number
  hc_a_per_m: number
  demag?: Array<{ temperature_c?: number; curve: CurveTable2D }>
  alphaBr?: number
  alphaHc?: number
}

export interface CoilProps {
  resistivity_ohm_m: number
  fillFactor?: number
  skin?: Record<string, unknown>
}

export interface AcimBarProps {
  conductivity_s_per_m: number
  skin?: Record<string, unknown>
}

export interface MaterialCurves {
  steel?: SteelProps
  magnet?: MagnetProps
  coil?: CoilProps
  acim_bar?: AcimBarProps
}

export interface Material {
  id: string
  name: string
  category: MaterialCategory
  builtin: boolean
  materialsSchemaVersion: MaterialsSchemaVersion | string
  curves?: MaterialCurves
  meta?: Record<string, unknown>
  deletedAt?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface MaterialListResponse {
  items: Material[]
}
