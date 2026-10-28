/** Thin types for /compare drive-mode side-by-side (fixture samples). */

export type CompareFamily = 'pm' | 'acim'

export type CompareDriveMode = 'bldc_square' | 'pmsm_foc' | 'acim_vf' | 'acim_foc'

export interface DriveWaveforms {
  t_s: number[]
  ia: number[]
  ib: number[]
  ic: number[]
  torque_nm: number[]
}

export interface DriveLossesW {
  copper?: number | null
  iron?: number | null
  magnetEddy?: number | null
  bar?: number | null
  endRing?: number | null
}

export interface DriveMetrics {
  torqueAvgNm?: number | null
  torqueRipplePpNm?: number | null
  /** alias seen in samples */
  ripplePpNm?: number | null
  pMechW?: number | null
  pElecW?: number | null
  efficiency?: number | null
  [key: string]: unknown
}

export interface DriveCurrentsA {
  rmsPhase?: number | null
  id?: number | null
  iq?: number | null
}

export interface DriveSampleResult {
  mode: CompareDriveMode | string
  machineType: string
  source?: string
  operatingPoint?: Record<string, unknown>
  metrics?: DriveMetrics
  lossesW?: DriveLossesW
  currentsA?: DriveCurrentsA
  waveforms?: DriveWaveforms
  pwm?: Record<string, unknown>
  meta?: Record<string, unknown>
  /** sample path when loaded from public/drive */
  _samplePath?: string
  [key: string]: unknown
}

export interface ComparePairDef {
  family: CompareFamily
  label: string
  a: { path: string; label: string }
  b: { path: string; label: string }
}

export const COMPARE_PAIRS: Record<CompareFamily, ComparePairDef> = {
  pm: {
    family: 'pm',
    label: '永磁',
    a: { path: '/drive/bldc_square_sample.json', label: 'BLDC 方波' },
    b: { path: '/drive/pmsm_foc_sample.json', label: 'PMSM FOC' },
  },
  acim: {
    family: 'acim',
    label: 'ACIM',
    a: { path: '/drive/acim_vf_sample.json', label: 'ACIM V/f' },
    b: { path: '/drive/acim_foc_sample.json', label: 'ACIM FOC' },
  },
}

export const LOSS_KEYS: (keyof DriveLossesW)[] = [
  'copper',
  'iron',
  'magnetEddy',
  'bar',
  'endRing',
]

export function lossesTotal(L?: DriveLossesW | null): number {
  if (!L) return 0
  let s = 0
  for (const k of LOSS_KEYS) {
    const v = L[k]
    if (typeof v === 'number' && Number.isFinite(v)) s += v
  }
  return s
}

export function ripplePp(m?: DriveMetrics | null): number | null {
  if (!m) return null
  const v = m.torqueRipplePpNm ?? m.ripplePpNm
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}
