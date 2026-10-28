/**
 * 分类自检（不进页面包）。覆盖 FEM tip 797ce67 真路径、heat-proxy、旧 fixture。
 * 运行：apps/web 下 esbuild 打包后 node 执行。
 */
import { buildFieldPostprocessView, type FieldPostprocessView } from './fieldPostprocess'
import type { FemManifest, FemScalarsArtifact } from '../types/fieldViz'

function fail(message: string): never {
  throw new Error(message)
}

function row(view: FieldPostprocessView, key: string) {
  const found = view.rows.find((item) => item.key === key)
  if (!found) fail(`missing row ${key} on ${view.kind}`)
  return found
}

function assertNoClaim(view: FieldPostprocessView) {
  const text = `${view.title}\n${view.note}\n${view.rows.map((item) => item.value).join('\n')}`
  if (text.includes('≤') || text.includes('3%') || /MVP\s*已/.test(text)) {
    fail(`claim-like copy: ${view.title}`)
  }
}

function manifest(scalars: Record<string, unknown>, extra: Partial<FemManifest> = {}): FemManifest {
  return {
    jobId: 'job',
    status: 'succeeded',
    solverKernel: 'elmer',
    topology: 'AF',
    machineType: 'PMSM',
    dim: '3d',
    artifacts: [],
    scalars,
    ...extra,
  }
}

function runFieldPostprocessChecks() {
  const smoke = JSON.parse(`{
    "equationMode": "magnetostatic",
    "magnetostaticPathReady": true,
    "pending_calibration": true,
    "dryRun": false,
    "elmerExit": 0,
    "axialForceN": -0.002726984380961,
    "bearingLoadN": null,
    "deflectionHintMm": null,
    "postprocess": "maxwell",
    "magneticEnergyJ": 9.236521314775e-05,
    "torqueNm": 0.0,
    "lossesW": {}
  }`) as FemScalarsArtifact

  const truePath = buildFieldPostprocessView(null, smoke)
  if (!truePath) fail('true path view')
  if (truePath.kind !== 'magnetostatic' || truePath.title !== '磁静力学后处理') fail(truePath.title)
  if (!truePath.pendingCalibration) fail('pending badge')
  if (row(truePath, 'postprocess').value !== 'maxwell') fail('postprocess')
  if (row(truePath, 'axialForceN').state !== 'set' || !row(truePath, 'axialForceN').uncalibrated) {
    fail('axial uncalibrated')
  }
  if (row(truePath, 'axialForceN').unit !== 'N') fail('axial unit')
  if (row(truePath, 'magneticEnergyJ').state !== 'set' || row(truePath, 'magneticEnergyJ').unit !== 'J') {
    fail('energy')
  }
  if (!row(truePath, 'magneticEnergyJ').uncalibrated) fail('energy pending')
  if (!row(truePath, 'magneticEnergyJ').value.includes('e')) fail(`energy format ${row(truePath, 'magneticEnergyJ').value}`)
  if (row(truePath, 'bearingLoadN').value !== 'null') fail('bearing null')
  if (row(truePath, 'dryRun').value !== 'false') fail('dryRun')
  if (row(truePath, 'elmerExit').value !== '0') fail('elmerExit')
  if (row(truePath, 'lossesW').value !== '{}') fail('losses')
  if (!truePath.note.includes('pending_calibration')) fail('note pending')
  assertNoClaim(truePath)

  const apiShape = buildFieldPostprocessView(
    manifest({
      dryRun: false,
      pending_calibration: true,
      equationMode: 'magnetostatic',
      magnetostaticPathReady: true,
      postprocess: 'maxwell',
      axialForceN: 12.5,
      magneticEnergyJ: 0.42,
      elmerExit: 0,
      torqueNm: 0,
    }),
    null,
  )
  if (!apiShape || apiShape.kind !== 'magnetostatic') fail('api manifest')
  if (row(apiShape, 'axialForceN').value !== '12.5' || row(apiShape, 'magneticEnergyJ').value !== '0.42') {
    fail('api numbers')
  }

  const shell = JSON.parse(`{
    "equationMode": "magnetostatic",
    "pending_calibration": true,
    "magnetostaticPathReady": true,
    "dryRun": true,
    "torqueNm": null,
    "axialForceN": null,
    "bearingLoadN": null,
    "deflectionHintMm": null,
    "lossesW": {}
  }`) as FemScalarsArtifact
  const shellView = buildFieldPostprocessView(null, shell)
  if (!shellView || shellView.kind !== 'magnetostatic') fail('shell kind')
  if (row(shellView, 'postprocess').state !== 'missing') fail('shell postprocess')
  if (row(shellView, 'magneticEnergyJ').state !== 'missing') fail('shell energy')
  if (row(shellView, 'axialForceN').value !== 'null' || !row(shellView, 'axialForceN').uncalibrated) {
    fail('shell axial')
  }
  if (!shellView.note.includes('dryRun=true')) fail('shell dry')
  assertNoClaim(shellView)

  const legacy = buildFieldPostprocessView(
    manifest({ torqueNm: 0, dryRun: true, pending_calibration: true }),
    { schemaVersion: 'fem-scalars-v0', torqueNm: 0, dryRun: true, notes: 'fixture dry-run; pending_calibration' },
  )
  if (!legacy || legacy.kind !== 'heat-proxy') fail('legacy kind')
  if (legacy.title !== 'heat-proxy / 非磁静力学真值') fail(legacy.title)
  if (legacy.equationMode !== 'missing') fail('legacy mode')
  if (!legacy.pendingCalibration) fail('legacy pending default')
  if (legacy.rows.some((item) => item.key === 'axialForceN' || item.key === 'magneticEnergyJ')) {
    fail('legacy must not present magnetostatic rows')
  }
  assertNoClaim(legacy)

  const heat = buildFieldPostprocessView(
    manifest({
      equationMode: 'heat_proxy',
      dryRun: false,
      pending_calibration: true,
      elmerExit: 0,
      torqueNm: 0,
      axialForceN: null,
      lossesW: {},
    }),
    null,
  )
  if (!heat || heat.kind !== 'heat-proxy' || heat.title.includes('磁静力学后处理')) fail('heat title')
  if (heat.note.includes('见到轴向力')) fail('null axial is not a stray value')
  assertNoClaim(heat)

  const stray = buildFieldPostprocessView(
    manifest({ equationMode: 'heat_proxy', axialForceN: 9, magneticEnergyJ: 1, pending_calibration: true }),
    null,
  )
  if (!stray || stray.kind !== 'heat-proxy') fail('stray kind')
  if (!stray.note.includes('仍不作为磁静力学真值')) fail('stray note')
  if (stray.rows.some((item) => item.key === 'axialForceN')) fail('stray row')

  const readyOnly = buildFieldPostprocessView(manifest({ magnetostaticPathReady: true }), null)
  if (!readyOnly || readyOnly.kind !== 'magnetostatic') fail('ready only')
  if (!readyOnly.pendingCalibration) fail('missing pending defaults true')

  const closed = buildFieldPostprocessView(
    manifest({
      equationMode: 'magnetostatic',
      magnetostaticPathReady: true,
      pending_calibration: false,
      axialForceN: 1,
      magneticEnergyJ: 2,
      postprocess: 'maxwell',
    }),
    null,
  )
  if (!closed || closed.pendingCalibration) fail('explicit false pending')
  if (row(closed, 'axialForceN').uncalibrated) fail('closed should not mark uncalibrated')

  const override = buildFieldPostprocessView(
    manifest({ equationMode: 'heat_proxy', pending_calibration: true }),
    { equationMode: 'magnetostatic', magnetostaticPathReady: true, postprocess: 'maxwell', axialForceN: 3 },
  )
  if (!override || override.kind !== 'magnetostatic' || row(override, 'postprocess').value !== 'maxwell') {
    fail('artifact overrides manifest')
  }
  if (!override.pendingCalibration) fail('pending kept from manifest when artifact omits it')

  const other = buildFieldPostprocessView(manifest({ equationMode: 'transient' }), null)
  if (!other || other.kind !== 'other' || other.title.includes('heat-proxy')) fail('other mode')
  assertNoClaim(other)
}

runFieldPostprocessChecks()
