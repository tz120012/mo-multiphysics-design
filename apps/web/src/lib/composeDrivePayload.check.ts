/**
 * composeDrivePayload 最小断言（不进页面包）。
 * 运行：cd apps/web && npx --yes esbuild src/lib/composeDrivePayload.check.ts --bundle --platform=node --format=esm --outfile=/tmp/composeDrivePayload.check.mjs && node /tmp/composeDrivePayload.check.mjs
 */
import { composeDrivePayloadFromUem } from './composeDrivePayload'

function fail(message: string): never {
  throw new Error(message)
}

function assertEq(actual: unknown, expected: unknown, label: string) {
  if (actual !== expected) fail(`${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
}

function run() {
  const pmsm = composeDrivePayloadFromUem({
    machineType: 'PMSM',
    excitation: {
      operatingPoint: { speed_rpm: 3000, current_a_peak: 25, gamma_deg: 0 },
      driveDraft: {
        mode: 'pmsm_foc',
        pwm: { carrierHz: 10000, modIndex: 0.9, scheme: 'svpwm' },
        deadTime: { tdeadUs: 1 },
        tempC: 80,
      },
    },
  })
  assertEq(pmsm.mode, 'pmsm_foc', 'pmsm.mode')
  assertEq(pmsm.machineType, 'PMSM', 'pmsm.machineType')
  assertEq(pmsm.operatingPoint?.speedRpm, 3000, 'speedRpm')
  assertEq(pmsm.operatingPoint?.iqA, 25, 'iqA from current_a_peak')
  assertEq(pmsm.operatingPoint?.gammaDeg, 0, 'gammaDeg')
  assertEq(pmsm.operatingPoint?.tempC, 80, 'tempC draft')
  assertEq(pmsm.pwm?.carrierHz, 10000, 'pwm.carrierHz')
  assertEq(pmsm.deadTime?.tdeadUs, 1, 'deadTime')

  const acim = composeDrivePayloadFromUem({
    machineType: 'ACIM',
    excitation: {
      operatingPoint: {
        speed_rpm: 1450,
        voltage_v_peak: 311,
        freq_hz: 50,
        slip: 0.03,
      },
      driveDraft: { mode: 'acim_vf' },
    },
  })
  assertEq(acim.mode, 'acim_vf', 'acim.mode')
  assertEq(acim.operatingPoint?.slip, 0.03, 'slip')
  assertEq(acim.operatingPoint?.voltageVPeak, 311, 'voltageVPeak')
  assertEq(acim.operatingPoint?.freqHz, 50, 'freqHz')

  const override = composeDrivePayloadFromUem({
    machineType: 'BLDC',
    excitation: {
      operatingPoint: { speed_rpm: 2000, current_a_peak: 10 },
      driveDraft: { mode: 'bldc_square', iqA: 18 },
    },
  })
  assertEq(override.operatingPoint?.iqA, 18, 'draft iqA overrides peak')

  console.log('composeDrivePayload.check: ok')
}

run()
