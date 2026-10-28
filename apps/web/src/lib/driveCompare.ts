import type { DriveCaseResult, DriveLossesW, DriveMetrics } from '@/api/types'

export type CompareScheme = 'pm' | 'acim'

export const COMPARE_URLS: Record<CompareScheme, { left: string; right: string; file: string }> = {
  pm: {
    left: '/drive/bldc_square_sample.json',
    right: '/drive/pmsm_foc_sample.json',
    file: 'compare_pm_bldc_vs_foc',
  },
  acim: {
    left: '/drive/acim_vf_sample.json',
    right: '/drive/acim_foc_sample.json',
    file: 'compare_acim_vf_vs_foc',
  },
}

export const DRIVE_MODE_LABEL: Record<string, string> = {
  bldc_square: 'BLDC 方波',
  pmsm_foc: 'PMSM FOC',
  acim_vf: 'ACIM V/f',
  acim_foc: '感应 FOC',
}

export const LOSS_KEYS = ['copper', 'iron', 'magnetEddy', 'bar', 'endRing'] as const
export type LossKey = (typeof LOSS_KEYS)[number]

export const LOSS_LABEL: Record<LossKey, string> = {
  copper: '铜耗',
  iron: '铁耗',
  magnetEddy: '永磁涡流',
  bar: '导条',
  endRing: '端环',
}

export function parseDriveCase(data: unknown): DriveCaseResult {
  if (!data || typeof data !== 'object') throw new Error('样例不是对象')
  const row = data as DriveCaseResult
  const w = row.waveforms
  if (!w || !Array.isArray(w.t_s) || !Array.isArray(w.torque_nm) || w.t_s.length < 2) {
    throw new Error('样例缺少 waveforms.t_s / torque_nm')
  }
  if (w.torque_nm.length !== w.t_s.length) throw new Error('torque_nm 长度与 t_s 不一致')
  return row
}

export function num(v: unknown): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}

export function ripplePp(m: DriveMetrics | undefined): number | null {
  return num(m?.torqueRipplePpNm) ?? num(m?.ripplePpNm)
}

export function lossOf(losses: DriveLossesW | undefined, key: LossKey): number | null {
  return num(losses?.[key])
}

export function lossTotal(losses: DriveLossesW | undefined): number {
  let sum = 0
  for (const key of LOSS_KEYS) {
    const v = lossOf(losses, key)
    if (v != null) sum += v
  }
  return sum
}

export interface MetricRow {
  key: string
  label: string
  unit: string
  digits: number
  asPercent?: boolean
  a: number | null
  b: number | null
}

export function compareRows(a: DriveCaseResult, b: DriveCaseResult): MetricRow[] {
  const rows: MetricRow[] = [
    row('speedRpm', '转速', 'rpm', 0, num(a.operatingPoint?.speedRpm), num(b.operatingPoint?.speedRpm)),
    row('torqueAvgNm', '平均转矩', 'N·m', 4, num(a.metrics?.torqueAvgNm), num(b.metrics?.torqueAvgNm)),
    row('torqueRipplePpNm', '脉动峰峰', 'N·m', 4, ripplePp(a.metrics), ripplePp(b.metrics)),
    row('pMechW', '机械功率', 'W', 2, num(a.metrics?.pMechW), num(b.metrics?.pMechW)),
    row('pElecW', '电功率', 'W', 2, num(a.metrics?.pElecW), num(b.metrics?.pElecW)),
    row('efficiency', '效率', '1', 2, num(a.metrics?.efficiency), num(b.metrics?.efficiency), true),
  ]
  for (const key of LOSS_KEYS) {
    const av = lossOf(a.lossesW, key)
    const bv = lossOf(b.lossesW, key)
    if (av == null && bv == null) continue
    rows.push(row(key, LOSS_LABEL[key], 'W', 3, av, bv))
  }
  rows.push(row('lossTotal', '总损耗', 'W', 3, lossTotal(a.lossesW), lossTotal(b.lossesW)))
  return rows
}

export function formatNum(v: number | null, digits: number, asPercent = false): string {
  if (v == null) return '—'
  const shown = asPercent ? v * 100 : v
  return shown.toFixed(digits)
}

export function formatDelta(a: number | null, b: number | null, digits: number, asPercent = false): string {
  if (a == null || b == null) return '—'
  const n = Number(((asPercent ? (a - b) * 100 : a - b)).toFixed(digits))
  if (n === 0) return (0).toFixed(digits)
  const text = Math.abs(n).toFixed(digits)
  return n > 0 ? `+${text}` : `-${text}`
}

export function compareCsv(a: DriveCaseResult, b: DriveCaseResult): string {
  const lines: string[] = []
  const push = (...cells: (string | number)[]) => {
    lines.push(cells.map(csvCell).join(','))
  }
  push('source', 'drive')
  push('left_mode', a.mode ?? '')
  push('left_machineType', a.machineType ?? '')
  push('right_mode', b.mode ?? '')
  push('right_machineType', b.machineType ?? '')
  lines.push('')
  push('key', 'label', 'unit', 'A', 'B', 'delta_A_minus_B')
  for (const r of compareRows(a, b)) {
    const pct = r.asPercent === true
    push(r.key, r.label, pct ? '%' : r.unit, formatNum(r.a, r.digits, pct), formatNum(r.b, r.digits, pct), formatDelta(r.a, r.b, r.digits, pct))
  }
  lines.push('')
  push('side', 'mode', 't_s', 'ia', 'ib', 'ic', 'torque_nm')
  appendWave(push, 'A', a)
  appendWave(push, 'B', b)
  return `${lines.join('\n')}\n`
}

function row(
  key: string,
  label: string,
  unit: string,
  digits: number,
  a: number | null,
  b: number | null,
  asPercent = false,
): MetricRow {
  return { key, label, unit, digits, a, b, ...(asPercent ? { asPercent } : {}) }
}

function csvCell(v: string | number): string {
  const text = String(v)
  if (/[",\n\r]/.test(text)) return `"${text.replace(/"/g, '""')}"`
  return text
}

function appendWave(
  push: (...cells: (string | number)[]) => void,
  side: string,
  item: DriveCaseResult,
) {
  const w = item.waveforms
  if (!w) return
  const n = w.t_s.length
  for (let i = 0; i < n; i++) {
    push(side, item.mode ?? '', w.t_s[i] ?? '', w.ia?.[i] ?? '', w.ib?.[i] ?? '', w.ic?.[i] ?? '', w.torque_nm[i] ?? '')
  }
}
