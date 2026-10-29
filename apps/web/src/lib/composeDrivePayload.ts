import type { DriveJobPayload, DriveMode, MachineType } from '@/api/types'
import type { UemExcitationState } from '@/lib/geometryDefaults'
import type { OperatingPoint } from '@/types/solver'

const DRIVE_MODES: readonly DriveMode[] = ['bldc_square', 'pmsm_foc', 'acim_vf', 'acim_foc']

function asDriveMode(raw: string | undefined, machineType: MachineType): DriveMode {
  if (raw && (DRIVE_MODES as readonly string[]).includes(raw)) return raw as DriveMode
  if (machineType === 'BLDC') return 'bldc_square'
  if (machineType === 'ACIM') return 'acim_vf'
  return 'pmsm_foc'
}

function num(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined
}

/**
 * UEM 激励切片 → 既有 DriveJobPayload（零新 API）。
 * operatingPoint 蛇形键 → drive 驼峰；driveDraft 覆盖优先。
 * source 不进 payload（Jobs 侧已有）。
 */
export function composeDrivePayloadFromUem(input: {
  machineType: MachineType
  excitation: UemExcitationState
  map?: {
    mapGrid?: Record<string, unknown>
    mapMode?: DriveMode
  }
}): DriveJobPayload {
  const { machineType, excitation, map } = input
  const op: OperatingPoint = excitation.operatingPoint ?? { speed_rpm: 0 }
  const draft = excitation.driveDraft
  const mode = map
    ? ('efficiency_map' as const)
    : asDriveMode(draft?.mode, machineType)

  const operatingPoint: Record<string, unknown> = {}
  const speedRpm = num(op.speed_rpm)
  if (speedRpm !== undefined) operatingPoint.speedRpm = speedRpm

  const torqueNm = num(draft?.torqueNm)
  if (torqueNm !== undefined) operatingPoint.torqueNm = torqueNm

  const tempC = num(draft?.tempC)
  if (tempC !== undefined) operatingPoint.tempC = tempC

  const resolvedMode = map?.mapMode ?? (mode === 'efficiency_map' ? asDriveMode(draft?.mode, machineType) : mode)

  // iqA / 电流峰值启发（BLDC / PMSM）；draft.iqA 优先
  const iqOverride = num(draft?.iqA)
  const peak = num(op.current_a_peak)
  if (iqOverride !== undefined) {
    operatingPoint.iqA = iqOverride
  } else if (
    peak !== undefined &&
    (resolvedMode === 'bldc_square' || resolvedMode === 'pmsm_foc' || resolvedMode === 'acim_foc')
  ) {
    operatingPoint.iqA = peak
  }

  const idA = num(draft?.idA)
  if (idA !== undefined) operatingPoint.idA = idA

  // ACIM：slip / 电压 / 频率进 operatingPoint
  const slip = num(draft?.slip) ?? num(op.slip)
  if (slip !== undefined) operatingPoint.slip = slip
  const vPeak = num(op.voltage_v_peak)
  if (vPeak !== undefined) operatingPoint.voltageVPeak = vPeak
  const freqHz = num(op.freq_hz)
  if (freqHz !== undefined) operatingPoint.freqHz = freqHz

  const gamma = num(op.gamma_deg)
  if (gamma !== undefined) operatingPoint.gammaDeg = gamma

  const payload: DriveJobPayload = {
    mode,
    machineType,
    operatingPoint,
  }

  if (draft?.pwm && typeof draft.pwm === 'object') {
    const pwm: Record<string, unknown> = {}
    if (num(draft.pwm.carrierHz) !== undefined) pwm.carrierHz = draft.pwm.carrierHz
    if (num(draft.pwm.modIndex) !== undefined) pwm.modIndex = draft.pwm.modIndex
    if (draft.pwm.scheme === 'svpwm' || draft.pwm.scheme === 'spwm') pwm.scheme = draft.pwm.scheme
    if (Object.keys(pwm).length) payload.pwm = pwm
  }

  if (draft?.deadTime && typeof draft.deadTime === 'object') {
    const tdeadUs = num(draft.deadTime.tdeadUs)
    if (tdeadUs !== undefined) payload.deadTime = { tdeadUs }
  }

  if (map) {
    payload.mapMode = map.mapMode ?? asDriveMode(draft?.mode, machineType)
    if (map.mapGrid) payload.mapGrid = { ...map.mapGrid }
  }

  return payload
}
