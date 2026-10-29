/**
 * Q7-3 同壳后处理可见文案。对齐 docs/drafts/Q7-3-同壳后处理-FEM协作.md §2。
 * 缺 equationMode 按 heat-proxy。不把 heat-proxy 写成磁静力学，不宣称精度。
 */
import type { EquationModeKind } from '@/lib/fieldPostprocess'

export type ShellFieldSource = 'loading' | 'fixture' | 'job-fixture' | 'job-artifacts'

export function femManifestRef(jobId: string): string {
  return `solver/fem/jobs/${jobId}/manifest.json`
}

export function shellHonestyLines(input: {
  jobId: string
  forceFixture: boolean
  source: ShellFieldSource
  equationMode: EquationModeKind | null
  dryRun: boolean
  fieldStale: boolean
  resultUpdated: boolean
}): string[] {
  const lines: string[] = []
  if (!input.jobId) {
    lines.push('未绑定 FEM job；当前为 public fixture / 演示数据。不宣称误差达标。')
  }
  if (input.forceFixture) {
    lines.push('显式强制 fixture。不是该 job 精简产物。')
  }
  if (input.source === 'job-fixture') {
    lines.push('已降级 public fixture（artifacts 不可达）。当前场数据不是该 job 精简产物。')
  }
  if (input.source === 'job-artifacts') {
    lines.push('来源 job-artifacts：已请求 GET /jobs/{id}/artifacts。不宣称误差达标。')
  }
  if (input.jobId && input.fieldStale) {
    lines.push('参数已变。当前场图仍绑定旧 job，不是当前参数结果。不得标「结果已更新」。')
  } else if (input.jobId && input.resultUpdated && input.source === 'job-artifacts') {
    lines.push('结果已更新（新 jobId）。不宣称误差达标。')
  }
  if (input.equationMode === 'magnetostatic') {
    lines.push(
      '磁静力学路径（有限边界）；pending_calibration — 不宣称整机 ≤3%/≤5%；F2 不可外推。',
    )
  } else if (input.equationMode === 'heat_proxy' || input.equationMode === 'missing') {
    lines.push('heat-proxy / 热方程调度路径，不是磁静力学真值。校准未关闭。')
  } else if (input.equationMode === 'other') {
    lines.push('equationMode 不是磁静力学真值。校准未关闭。')
  }
  if (input.dryRun) {
    lines.push('dry-run：未调 Elmer；仅契约/调度。')
  }
  return lines
}
