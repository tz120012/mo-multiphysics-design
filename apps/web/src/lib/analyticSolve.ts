/**
 * Local-first 径向解析适配层（Q2）。
 *
 * 交互求解降级序（钉死，见 docs/drafts/Q2-材料与解析边界.md §3.3）：
 *   1. Wasm（browser）— 包尚未到；stub tryLoad，失败则降级
 *   2. sync POST /api/v1/solver/analytic/solve?solver=mec — tip 8b71df1 已接线 Python 金标；
 *      真结果优先（meta.source=sync，保留金标 meta.mock=false）；404/501/网络失败才降级
 *   3. Jobs analytic — **禁止**阻塞 UI 等轮询才改结果（本层不 await Jobs）
 *   4. 本地 fixture/mock 兜底（仅 sync 失败时；PMSM/ACIM fixture 缩放；BLDC 客户端 mock）
 *
 * Motor：主路径为 sync mec；Wasm 待包；fixture/mock 仅回退。
 */
import { isAxiosError } from 'axios'
import { postAnalyticSolve } from '@/api/solver'
import { cloneJson } from '@/lib/paramPath'
import { solveWithWasm } from '@/lib/solverWasm'
import type {
  MachineType,
  SolveBackend,
  SolveRequest,
  SolveResult,
  SweepPoint,
} from '@/types/solver'
import { SOLVE_SCHEMA_VERSION } from '@/types/solver'

const PMSM_FIXTURE_URL = '/solver/radial_pmsm_mec_fixture.json'
const ACIM_FIXTURE_URL = '/solver/radial_acim_equiv_fixture.json'

/** PMSM fixture 对应样例工况（radial_pmsm_request.json） */
const PMSM_FIXTURE_SPEED_RPM = 3000
const PMSM_FIXTURE_CURRENT_A = 25

/** ACIM fixture 对应样例工况（radial_acim_request.json） */
const ACIM_FIXTURE_VOLTAGE_V = 311
const ACIM_FIXTURE_FREQ_HZ = 50
const ACIM_FIXTURE_SLIP = 1 / 30 // (1500-1450)/1500

let cachedPmsmFixture: SolveResult | null = null
let cachedAcimFixture: SolveResult | null = null

/** 最近一次交互求解实际使用的路径（供 UI 展示） */
let lastSolveBackend: SolveBackend | null = null

export function getSolveBackend(): SolveBackend | null {
  return lastSolveBackend
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
    throw new Error(`Q2 仅支持径向 RF，当前 topology=${request.topology}`)
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

function tagSource(result: SolveResult, source: SolveBackend, elapsedMs?: number): SolveResult {
  const meta = {
    ...result.meta,
    source,
    elapsed_ms: elapsedMs ?? result.meta.elapsed_ms,
  }
  if (source === 'fixture' || source === 'mock') {
    meta.mock = true
  }
  return { ...result, meta }
}

async function loadPmsmFixture(): Promise<SolveResult> {
  if (cachedPmsmFixture) return cloneJson(cachedPmsmFixture)
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
  return cloneJson(data)
}

async function loadAcimFixture(): Promise<SolveResult> {
  if (cachedAcimFixture) return cloneJson(cachedAcimFixture)
  const res = await fetch(ACIM_FIXTURE_URL)
  if (!res.ok) {
    throw new Error(`无法加载 ACIM fixture（${res.status}）：${ACIM_FIXTURE_URL}`)
  }
  const data = (await res.json()) as SolveResult
  if (data.schema_version !== SOLVE_SCHEMA_VERSION) {
    throw new Error(
      `fixture schema_version 不匹配：期望 ${SOLVE_SCHEMA_VERSION}，得到 ${data.schema_version}`,
    )
  }
  cachedAcimFixture = data
  return cloneJson(data)
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
  const current = op.current_a_peak ?? PMSM_FIXTURE_CURRENT_A
  const br = request.materials.br_t ?? 1.2
  const br0 = 1.2

  const kI = current / PMSM_FIXTURE_CURRENT_A
  const kN = speed / PMSM_FIXTURE_SPEED_RPM
  const kBr = br / br0

  const torque = base.torque_nm * kI * kBr
  const bemf = base.back_emf_v_peak * kN * kBr
  const copper = base.losses_w.copper * kI * kI
  const iron = base.losses_w.iron * Math.abs(kN)
  const magnetEddy = (base.losses_w.magnet_eddy ?? 0) * kN * kN * kBr * kBr

  return {
    schema_version: SOLVE_SCHEMA_VERSION,
    meta: {
      solver: 'mec',
      elapsed_ms: elapsedMs,
      mock: true,
      source: 'fixture',
      note:
        'PMSM：sync/Wasm 失败后的本地 MEC fixture 粗缩放兜底（approximate）。主路径为 sync?solver=mec（8b71df1）。见 docs/drafts/Q2-材料与解析边界.md。',
      mec: base.meta.mec,
    },
    torque_nm: torque,
    back_emf_v_peak: bemf,
    losses_w: {
      copper,
      iron,
      magnet_eddy: magnetEddy,
    },
    inductance_h: base.inductance_h ? { ...base.inductance_h } : undefined,
  }
}

/**
 * ACIM：以 acim_equiv fixture 为基线粗缩放（与 PMSM 对称）。
 * T ∝ (V/V0)² · slip_shape；E ∝ V·(1-s)；铜/铁/导条按 V、f、slip 粗比例。
 */
function scaleAcimFromFixture(
  base: SolveResult,
  request: SolveRequest,
  elapsedMs: number,
): SolveResult {
  const op = request.operating_point
  const speed = Math.max(0, op.speed_rpm)
  const V = op.voltage_v_peak ?? ACIM_FIXTURE_VOLTAGE_V
  const freq = op.freq_hz ?? ACIM_FIXTURE_FREQ_HZ
  const poles = request.geometry.poles
  const nSync = (120 * freq) / Math.max(2, poles)
  const slip =
    op.slip != null
      ? Math.max(1e-4, Math.min(0.99, op.slip))
      : nSync > 0
        ? Math.max(1e-4, Math.min(0.99, (nSync - speed) / nSync))
        : ACIM_FIXTURE_SLIP

  const kV = V / ACIM_FIXTURE_VOLTAGE_V
  const kF = freq / ACIM_FIXTURE_FREQ_HZ
  const s0 = ACIM_FIXTURE_SLIP
  const spk = 0.12
  // 相对 fixture 的 slip 转矩形状比（同 Tpk 归一化）
  const shape = (s: number) => (2 * s * spk) / (s * s + spk * spk)
  const kSlip = shape(slip) / shape(s0)

  const torque = base.torque_nm * kV * kV * kSlip
  const bemf = base.back_emf_v_peak * kV * ((1 - slip) / (1 - s0))
  const copper = base.losses_w.copper * kV * kV
  const iron = base.losses_w.iron * Math.abs(kF)
  const rotorBar = (base.losses_w.rotor_bar ?? 0) * kV * kV * (slip / s0)

  return {
    schema_version: SOLVE_SCHEMA_VERSION,
    meta: {
      solver: 'acim_equiv',
      elapsed_ms: elapsedMs,
      mock: true,
      source: 'fixture',
      note:
        'ACIM：sync/Wasm 失败后的本地 acim_equiv fixture 粗缩放兜底（approximate）。主路径为 sync?solver=mec（8b71df1）。见 docs/drafts/Q2-材料与解析边界.md。',
      acim: {
        ...(typeof base.meta.acim === 'object' && base.meta.acim ? base.meta.acim : {}),
        slip,
        freq_hz: freq,
        n_sync_rpm: nSync,
        scaled: true,
      },
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

/** 几何粗缩放因子（相对样例尺寸），仅 BLDC mock 用 */
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

  const kt = 0.12 * br * (turns / 40) * (poles / 8) * gs
  const ke = kt * 0.10472
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
      source: 'mock',
      note: 'BLDC：sync/Wasm 失败后的客户端 mock 兜底（合理数量级）。',
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

/** ACIM 无 fixture 时的最终 mock 兜底（一般不会走到） */
function mockAcim(request: SolveRequest, elapsedMs: number): SolveResult {
  const op = request.operating_point
  const speed = Math.max(0, op.speed_rpm)
  const slip = op.slip ?? 0.03
  const I = op.current_a_peak ?? 15
  const gs = geometryScale(request)
  const poles = request.geometry.poles

  const s = Math.max(1e-4, Math.min(0.99, slip))
  const spk = 0.12
  const Tpk = 8.5 * gs * (poles / 4)
  const torque = Tpk * ((2 * s * spk) / (s * s + spk * spk)) * (I / 15)

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
      source: 'mock',
      note: 'ACIM：客户端 mock 兜底（fixture 不可用时）。见 docs/drafts/Q2-材料与解析边界.md。',
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

async function trySyncSolve(request: SolveRequest): Promise<SolveResult | null> {
  try {
    // tip 8b71df1：sync 真端已上；显式 solver=mec 打 Python 金标
    const result = await postAnalyticSolve(request, { solver: 'mec' })
    // source=sync；不强制改 mock，保留金标 meta.mock=false
    return tagSource(result, 'sync')
  } catch (err) {
    if (isAxiosError(err)) {
      const status = err.response?.status
      // 404/501/5xx/网络失败 → 降级；其它 4xx 也降级以免卡 UI
      if (status === 404 || status === 501 || status == null || status >= 400) {
        return null
      }
    }
    return null
  }
}

async function solveLocalFallback(request: SolveRequest, t0: number): Promise<SolveResult> {
  switch (request.machine_type as MachineType) {
    case 'PMSM': {
      const base = await loadPmsmFixture()
      return scalePmsmFromFixture(base, request, nowMs() - t0)
    }
    case 'ACIM': {
      try {
        const base = await loadAcimFixture()
        return scaleAcimFromFixture(base, request, nowMs() - t0)
      } catch {
        return mockAcim(request, nowMs() - t0)
      }
    }
    case 'BLDC':
      return mockBldc(request, nowMs() - t0)
    default:
      throw new Error(`不支持的 machine_type：${(request as SolveRequest).machine_type}`)
  }
}

/**
 * 径向求解入口 — Wasm → sync(mec 金标) → fixture/mock 降级。
 * sync 成功优先（真结果）；**不** await Jobs HTTP。
 */
export async function solveRadial(request: SolveRequest): Promise<SolveResult> {
  assertRadialRf(request)
  const t0 = nowMs()

  // 1. Wasm
  try {
    const wasmResult = await solveWithWasm(request)
    if (wasmResult) {
      const tagged = tagSource(wasmResult, 'wasm', nowMs() - t0)
      lastSolveBackend = 'wasm'
      return tagged
    }
  } catch {
    /* stub / load fail → degrade */
  }

  // 2. sync POST /solver/analytic/solve
  const syncResult = await trySyncSolve(request)
  if (syncResult) {
    lastSolveBackend = 'sync'
    return {
      ...syncResult,
      meta: { ...syncResult.meta, elapsed_ms: syncResult.meta.elapsed_ms || nowMs() - t0 },
    }
  }

  // 3. Jobs — 故意不 await；交互路径跳过
  // （可选 fire-and-forget 由上层自行决定，本适配层不发起）

  // 4. fixture / mock
  const local = await solveLocalFallback(request, t0)
  lastSolveBackend = local.meta.source ?? (local.meta.mock ? 'mock' : 'fixture')
  return local
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
    if (request.machine_type === 'ACIM') {
      const slip =
        req.operating_point.slip ??
        (typeof r.meta.acim?.slip === 'number' ? r.meta.acim.slip : undefined)
      if (slip != null) pt.slip = slip
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
