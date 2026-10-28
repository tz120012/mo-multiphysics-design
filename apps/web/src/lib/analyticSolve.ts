/**
 * Local-first 径向解析适配层（Q2-4）。
 * 不把 POST /jobs 当真相源；预留同一 SolveResult 形状，便于日后 jobs.analytic 填表。
 */
import type {
  MachineType,
  SolveRequest,
  SolveResult,
  SweepPoint,
} from '@/types/solver'
import { SOLVE_SCHEMA_VERSION } from '@/types/solver'

const PMSM_FIXTURE_URL = '/solver/radial_pmsm_mec_fixture.json'

/** Fixture 对应样例工况（radial_pmsm_request.json） */
const FIXTURE_SPEED_RPM = 3000
const FIXTURE_CURRENT_A = 25

let cachedPmsmFixture: SolveResult | null = null

async function loadPmsmFixture(): Promise<SolveResult> {
  if (cachedPmsmFixture) return structuredClone(cachedPmsmFixture)
  const res = await fetch(PMSM_FIXTURE_URL)
  if (!res.ok) {
    throw new Error(`无法加载 PMSM MEC fixture（${res.status}）：${PMSM_FIXTURE_URL}`)
  }
  const data = (await res.json()) as SolveResult
  if (data.schema_version !== SOLVE_SCHEMA_VERSION) {
    throw new Error(
      `fixture schema_version 不匹配：期望 ${SOLVE_SCHEMA_VERSION}，得到 ${data.schema_version}`,
    )
  }
  cachedPmsmFixture = data
  return structuredClone(data)
}

function nowMs(): number {
  return typeof performance !== 'undefined' ? performance.now() : Date.now()
}

function assertRadialRf(request: SolveRequest): void {
  if (request.schema_version !== SOLVE_SCHEMA_VERSION) {
    throw new Error(
      `不支持的 schema_version：${request.schema_version}（仅 ${SOLVE_SCHEMA_VERSION}）`,
    )
  }
  if (request.topology !== 'RF') {
    throw new Error(`Q2-4 仅支持径向 RF，当前 topology=${request.topology}`)
  }
  const g = request.geometry
  if (!(g.poles >= 2 && g.slots >= 3)) {
    throw new Error('geometry.poles≥2 且 slots≥3')
  }
  for (const [k, v] of Object.entries({
    stack_length_m: g.stack_length_m,
    airgap_m: g.airgap_m,
    rotor_od_m: g.rotor_od_m,
    stator_id_m: g.stator_id_m,
  })) {
    if (!(typeof v === 'number' && v > 0)) {
      throw new Error(`geometry.${k} 须 > 0`)
    }
  }
}

/**
 * 按工况对 MEC fixture 做粗比例缩放（approximate，非真核重算）。
 * T ∝ I·Br；E ∝ n·Br；铜耗 ∝ I²；铁耗 ∝ n；磁涡流 ∝ n²。
 */
function scalePmsmFromFixture(
  base: SolveResult,
  request: SolveRequest,
  elapsedMs: number,
): SolveResult {
  const op = request.operating_point
  const speed = op.speed_rpm
  const current = op.current_a_peak ?? FIXTURE_CURRENT_A
  const br = request.materials.br_t ?? 1.2
  const br0 = 1.2

  const kI = current / FIXTURE_CURRENT_A
  const kN = speed / FIXTURE_SPEED_RPM
  const kBr = br / br0

  const torque = base.torque_nm * kI * kBr
  const bemf = base.back_emf_v_peak * kN * kBr
  const copper = base.losses_w.copper * kI * kI
  const iron = base.losses_w.iron * Math.abs(kN)
  const magnetEddy =
    (base.losses_w.magnet_eddy ?? 0) * kN * kN * kBr * kBr

  return {
    schema_version: SOLVE_SCHEMA_VERSION,
    meta: {
      solver: 'mec',
      elapsed_ms: elapsedMs,
      mock: true,
      note:
        'PMSM：以本地 MEC fixture 为基线，按 speed/current/Br 粗比例缩放（approximate，非真核重算）。待 Mo-解析 Wasm/HTTP 接入后替换。',
    },
    torque_nm: torque,
    back_emf_v_peak: bemf,
    losses_w: {
      copper,
      iron,
      magnet_eddy: magnetEddy,
    },
    inductance_h: base.inductance_h
      ? { ...base.inductance_h }
      : undefined,
  }
}

/** 几何粗缩放因子（相对样例尺寸），仅 mock 用 */
function geometryScale(request: SolveRequest): number {
  const g = request.geometry
  const L0 = 0.04
  const D0 = 0.06
  return (g.stack_length_m / L0) * (g.rotor_od_m / D0) ** 2
}

function mockBldc(request: SolveRequest, elapsedMs: number): SolveResult {
  const op = request.operating_point
  const speed = Math.max(0, op.speed_rpm)
  const I = op.current_a_peak ?? 20
  const br = request.materials.br_t ?? 1.1
  const turns = request.geometry.turns_per_phase ?? 40
  const poles = request.geometry.poles
  const gs = geometryScale(request)

  // 数量级合理的客户端 mock（非 MEC）
  const kt = 0.12 * br * (turns / 40) * (poles / 8) * gs
  const ke = kt * 0.10472 // ≈ Vpeak / (rad/s) 粗对应
  const omega = (speed * Math.PI) / 30
  const torque = kt * I
  const bemf = ke * omega
  const copper = 0.08 * I * I * (turns / 40)
  const iron = 0.012 * speed * br * br * gs
  const magnetEddy = 2e-8 * speed * speed * br * br * gs

  return {
    schema_version: SOLVE_SCHEMA_VERSION,
    meta: {
      solver: 'mock',
      elapsed_ms: elapsedMs,
      mock: true,
      note: 'BLDC：客户端 mock（合理数量级），待 Mo-解析真核。',
    },
    torque_nm: torque,
    back_emf_v_peak: bemf,
    losses_w: {
      copper,
      iron,
      magnet_eddy: magnetEddy,
    },
  }
}

function mockAcim(request: SolveRequest, elapsedMs: number): SolveResult {
  const op = request.operating_point
  const speed = Math.max(0, op.speed_rpm)
  const slip = op.slip ?? 0.03
  const I = op.current_a_peak ?? 15
  const gs = geometryScale(request)
  const poles = request.geometry.poles

  // 简化：T ≈ Tpk * (2s·spk)/(s²+spk²) 形状；额定附近
  const s = Math.max(1e-4, Math.min(0.99, slip))
  const spk = 0.12
  const Tpk = 8.5 * gs * (poles / 4)
  const torque = Tpk * ((2 * s * spk) / (s * s + spk * spk)) * (I / 15)

  // 同步速粗估：n_sync ≈ speed / (1-s)；反电势用端电压份额代替感应电势量级
  const V = op.voltage_v_peak ?? 311
  const bemf = V * (1 - s) * 0.85
  const copper = 1.2 * I * I * gs
  const iron = 0.02 * speed * gs
  const rotorBar = copper * 0.7 * (s / 0.03)

  return {
    schema_version: SOLVE_SCHEMA_VERSION,
    meta: {
      solver: 'mock',
      elapsed_ms: elapsedMs,
      mock: true,
      note: 'ACIM：客户端 mock（含 slip→转矩形状），待 Mo-解析等效电路真核 / fixture。',
    },
    torque_nm: torque,
    back_emf_v_peak: bemf,
    losses_w: {
      copper,
      iron,
      rotor_bar: rotorBar,
    },
  }
}

/**
 * 径向求解入口。PMSM 用 MEC fixture + 工况缩放；BLDC/ACIM 为客户端 mock。
 * 日后可改为同一签名调用 jobs.analytic，仍返回 SolveResult。
 */
export async function solveRadial(request: SolveRequest): Promise<SolveResult> {
  assertRadialRf(request)
  const t0 = nowMs()

  switch (request.machine_type as MachineType) {
    case 'PMSM': {
      const base = await loadPmsmFixture()
      const elapsed = nowMs() - t0
      return scalePmsmFromFixture(base, request, elapsed)
    }
    case 'BLDC':
      return mockBldc(request, nowMs() - t0)
    case 'ACIM':
      return mockAcim(request, nowMs() - t0)
    default:
      throw new Error(`不支持的 machine_type：${(request as SolveRequest).machine_type}`)
  }
}

/**
 * 转速扫描：多次改 operating_point.speed_rpm 调求解拼点（非单次结果带数组）。
 */
export async function sweepSpeed(
  request: SolveRequest,
  speeds: number[],
): Promise<SweepPoint[]> {
  assertRadialRf(request)
  if (!speeds.length) return []

  const points: SweepPoint[] = []
  for (const speed_rpm of speeds) {
    const req: SolveRequest = {
      ...request,
      geometry: { ...request.geometry },
      materials: { ...request.materials },
      operating_point: {
        ...request.operating_point,
        speed_rpm,
      },
    }
    const r = await solveRadial(req)
    const pt: SweepPoint = {
      speed_rpm,
      torque_nm: r.torque_nm,
      back_emf_v_peak: r.back_emf_v_peak,
    }
    if (request.machine_type === 'ACIM' && req.operating_point.slip != null) {
      pt.slip = req.operating_point.slip
    }
    points.push(pt)
  }
  return points
}

/** 默认扫描转速序列（rpm） */
export function defaultSpeedSweep(centerRpm: number): number[] {
  const c = Math.max(100, centerRpm)
  const steps = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
  return steps.map((k) => Math.round(c * k))
}
