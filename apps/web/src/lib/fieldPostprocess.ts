/**
 * `/field` 磁静力学后处理读数（Q5-2 FE）。
 * 只解释已有 F1 scalars / manifest，不新请求。对齐 FEM tip `797ce67`：
 * equationMode=magnetostatic、magnetostaticPathReady、postprocess=maxwell、
 * axialForceN、magneticEnergyJ、dryRun、elmerExit；pending_calibration 未关。
 * 缺 equationMode 的旧 fixture 按 heat-proxy 兼容路径，不标成磁静力学真值。
 */
import type { FemManifest, FemPostprocessFields, FemScalarsArtifact } from '@/types/fieldViz'

export const FEM_POSTPROCESS_KEYS = [
  'equationMode',
  'magnetostaticPathReady',
  'pending_calibration',
  'dryRun',
  'elmerExit',
  'axialForceN',
  'bearingLoadN',
  'deflectionHintMm',
  'postprocess',
  'torqueNm',
  'magneticEnergyJ',
  'lossesW',
] as const

export type FemPostprocessKey = (typeof FEM_POSTPROCESS_KEYS)[number]

/** 真路径数值在校准关闭前必须跟着 pending_calibration，不能单独当已校准结果。 */
const UNCALIBRATED_KEYS = new Set<FemPostprocessKey>(['axialForceN', 'magneticEnergyJ'])

const MAGNETOSTATIC_ROW_KEYS: readonly FemPostprocessKey[] = [
  'postprocess',
  'axialForceN',
  'magneticEnergyJ',
  'bearingLoadN',
  'deflectionHintMm',
  'torqueNm',
  'lossesW',
  'dryRun',
  'elmerExit',
]

const HEAT_PROXY_ROW_KEYS: readonly FemPostprocessKey[] = [
  'dryRun',
  'elmerExit',
  'torqueNm',
  'lossesW',
]

const UNITS: Partial<Record<FemPostprocessKey, string>> = {
  axialForceN: 'N',
  magneticEnergyJ: 'J',
  bearingLoadN: 'N',
  deflectionHintMm: 'mm',
  torqueNm: 'N·m',
}

const STRAY_KEYS: readonly FemPostprocessKey[] = [
  'postprocess',
  'axialForceN',
  'bearingLoadN',
  'deflectionHintMm',
  'magneticEnergyJ',
]

export type FieldPostprocessKind = 'magnetostatic' | 'heat-proxy' | 'other'

export type EquationModeKind = 'magnetostatic' | 'heat_proxy' | 'missing' | 'other'

export type ScalarState = 'missing' | 'null' | 'set'

export type FieldPostprocessRow = {
  key: FemPostprocessKey
  value: string
  state: ScalarState
  unit?: string
  /** 数值已写出，但 pending_calibration 仍在，不能当已校准。 */
  uncalibrated: boolean
}

export type FieldPostprocessView = {
  kind: FieldPostprocessKind
  title: string
  note: string
  pendingCalibration: boolean
  equationMode: EquationModeKind
  equationModeText: string
  pathReadyText: string
  rows: FieldPostprocessRow[]
}

type Slot = { present: boolean; value: unknown }

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

function slotFor(sources: Array<Record<string, unknown> | null | undefined>, key: string): Slot {
  let present = false
  let value: unknown
  for (const src of sources) {
    if (!src || !Object.prototype.hasOwnProperty.call(src, key)) continue
    present = true
    value = src[key]
  }
  return present ? { present: true, value } : { present: false, value: undefined }
}

/** manifest 根上的可选键（若写出方放在 scalars 外）。只收类型匹配的值。 */
export function assignManifestPostprocessFields(
  target: FemPostprocessFields,
  raw: Record<string, unknown>,
): void {
  if (typeof raw.equationMode === 'string') target.equationMode = raw.equationMode
  if (typeof raw.magnetostaticPathReady === 'boolean') {
    target.magnetostaticPathReady = raw.magnetostaticPathReady
  }
  if (typeof raw.pending_calibration === 'boolean') {
    target.pending_calibration = raw.pending_calibration
  }
  if (typeof raw.dryRun === 'boolean') target.dryRun = raw.dryRun
  if (Object.prototype.hasOwnProperty.call(raw, 'postprocess')) {
    const post = raw.postprocess
    if (post === null || typeof post === 'string') target.postprocess = post
  }
  if (isRecord(raw.lossesW)) target.lossesW = raw.lossesW
  assignNumber(target, raw, 'elmerExit')
  assignNumber(target, raw, 'axialForceN')
  assignNumber(target, raw, 'bearingLoadN')
  assignNumber(target, raw, 'deflectionHintMm')
  assignNumber(target, raw, 'torqueNm')
  assignNumber(target, raw, 'magneticEnergyJ')
}

function assignNumber(
  target: FemPostprocessFields,
  raw: Record<string, unknown>,
  key: 'elmerExit' | 'axialForceN' | 'bearingLoadN' | 'deflectionHintMm' | 'torqueNm' | 'magneticEnergyJ',
): void {
  if (!Object.prototype.hasOwnProperty.call(raw, key)) return
  const value = raw[key]
  if (value === null || (typeof value === 'number' && Number.isFinite(value))) {
    target[key] = value
  }
}

function manifestRootRecord(manifest: FemManifest | null): Record<string, unknown> | null {
  if (!manifest) return null
  const bag = manifest as FemManifest & Record<string, unknown>
  const out: Record<string, unknown> = {}
  for (const key of FEM_POSTPROCESS_KEYS) {
    if (Object.prototype.hasOwnProperty.call(bag, key)) out[key] = bag[key]
  }
  return out
}

export function normalizeEquationMode(raw: unknown, present: boolean): EquationModeKind {
  if (!present || raw === null || raw === undefined) return 'missing'
  if (typeof raw !== 'string') return 'other'
  const compact = raw.trim().toLowerCase().replace(/[-_\s]/g, '')
  if (!compact) return 'missing'
  if (compact === 'magnetostatic') return 'magnetostatic'
  if (compact === 'heatproxy') return 'heat_proxy'
  return 'other'
}

function equationModeText(kind: EquationModeKind, raw: unknown): string {
  if (kind === 'magnetostatic') return 'magnetostatic'
  if (kind === 'heat_proxy') return 'heat_proxy'
  if (kind === 'missing') return '未标注（兼容旧路径）'
  if (typeof raw === 'string' && raw.trim()) return raw.trim()
  return '未标注（兼容旧路径）'
}

/** 缺键默认未校准。只有显式 false 才关掉徽章。 */
function pendingCalibration(slot: Slot): boolean {
  if (!slot.present) return true
  return slot.value !== false
}

function pathReadyText(slot: Slot): string {
  if (!slot.present) return '—'
  if (slot.value === true) return 'true'
  if (slot.value === false) return 'false'
  if (slot.value === null) return 'null'
  return '—'
}

export function formatPostprocessValue(value: unknown, present: boolean): { value: string; state: ScalarState } {
  if (!present) return { value: '—', state: 'missing' }
  if (value === null) return { value: 'null', state: 'null' }
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return { value: String(value), state: 'set' }
    const abs = Math.abs(value)
    if (value !== 0 && (abs < 1e-3 || abs >= 1e6)) {
      return { value: value.toExponential(6), state: 'set' }
    }
    return { value: String(value), state: 'set' }
  }
  if (typeof value === 'boolean') return { value: value ? 'true' : 'false', state: 'set' }
  if (typeof value === 'string') {
    if (!value) return { value: '—', state: 'missing' }
    return { value, state: 'set' }
  }
  if (typeof value === 'object') {
    try {
      return { value: JSON.stringify(value), state: 'set' }
    } catch {
      return { value: '—', state: 'missing' }
    }
  }
  return { value: String(value), state: 'set' }
}

function hasStrayValue(sources: Array<Record<string, unknown> | null | undefined>): boolean {
  return STRAY_KEYS.some((key) => {
    const slot = slotFor(sources, key)
    if (!slot.present || slot.value === null || slot.value === undefined) return false
    if (typeof slot.value === 'string' && !slot.value.trim()) return false
    if (typeof slot.value === 'object' && !Array.isArray(slot.value)) {
      return Object.keys(slot.value as Record<string, unknown>).length > 0
    }
    return true
  })
}

function buildRows(
  keys: readonly FemPostprocessKey[],
  sources: Array<Record<string, unknown> | null | undefined>,
  pending: boolean,
): FieldPostprocessRow[] {
  return keys.map((key) => {
    const slot = slotFor(sources, key)
    const formatted = formatPostprocessValue(slot.value, slot.present)
    const uncalibrated = pending && UNCALIBRATED_KEYS.has(key)
    const unit = formatted.state === 'set' ? UNITS[key] : undefined
    return {
      key,
      value: formatted.value,
      state: formatted.state,
      ...(unit ? { unit } : {}),
      uncalibrated,
    }
  })
}

/**
 * manifest 根 < manifest.scalars < scalars 产物。
 * 后写的源只覆盖自己带上的键，缺键不擦掉前面的值。
 */
export function buildFieldPostprocessView(
  manifest: FemManifest | null,
  scalars: FemScalarsArtifact | null,
): FieldPostprocessView | null {
  if (!manifest && !scalars) return null
  const scalarRecord = isRecord(manifest?.scalars) ? manifest.scalars : null
  const artifactRecord = isRecord(scalars) ? (scalars as Record<string, unknown>) : null
  const sources = [manifestRootRecord(manifest), scalarRecord, artifactRecord]

  const modeSlot = slotFor(sources, 'equationMode')
  const readySlot = slotFor(sources, 'magnetostaticPathReady')
  const pendingSlot = slotFor(sources, 'pending_calibration')
  const drySlot = slotFor(sources, 'dryRun')

  const equationMode = normalizeEquationMode(modeSlot.value, modeSlot.present)
  const readyTrue = readySlot.present && readySlot.value === true
  const readyFalse = readySlot.present && readySlot.value === false
  const magnetostatic = equationMode === 'magnetostatic' || readyTrue
  const pending = pendingCalibration(pendingSlot)
  const modeText = equationModeText(equationMode, modeSlot.value)

  const disclaimer = '不宣称误差达标，不宣称 MVP。'
  let kind: FieldPostprocessKind
  let title: string
  let note: string
  let rows: FieldPostprocessRow[]

  if (magnetostatic) {
    kind = 'magnetostatic'
    title = '磁静力学后处理'
    const bits = ['磁静力学后处理标量来自 scalars 或 manifest。']
    if (drySlot.present && drySlot.value === true) bits.push('dryRun=true，不作为已标定真值。')
    if (readyFalse) bits.push('magnetostaticPathReady=false。')
    if (pending) {
      bits.push('axialForceN / magneticEnergyJ 未校准（pending_calibration）。')
    }
    bits.push(disclaimer)
    note = bits.join('')
    rows = buildRows(MAGNETOSTATIC_ROW_KEYS, sources, pending)
  } else if (equationMode === 'heat_proxy' || equationMode === 'missing') {
    kind = 'heat-proxy'
    title = 'heat-proxy / 非磁静力学真值'
    const bits = ['heat-proxy / 非磁静力学真值。']
    if (equationMode === 'missing') {
      bits.push('未标注 equationMode，按兼容旧路径理解，不是磁静力学真值。')
    } else {
      bits.push('equationMode=heat_proxy，不是磁静力学真值。')
    }
    if (pending) bits.push('校准未关闭。')
    if (hasStrayValue(sources)) {
      bits.push('见到轴向力、磁能或 postprocess 数值，仍不作为磁静力学真值。')
    }
    bits.push(disclaimer)
    note = bits.join('')
    rows = buildRows(HEAT_PROXY_ROW_KEYS, sources, false)
  } else {
    kind = 'other'
    title = '非磁静力学真值'
    note = `equationMode=${modeText}，不是磁静力学真值。${pending ? '校准未关闭。' : ''}${disclaimer}`
    rows = buildRows(HEAT_PROXY_ROW_KEYS, sources, false)
  }

  return {
    kind,
    title,
    note,
    pendingCalibration: pending,
    equationMode,
    equationModeText: modeText,
    pathReadyText: pathReadyText(readySlot),
    rows,
  }
}
