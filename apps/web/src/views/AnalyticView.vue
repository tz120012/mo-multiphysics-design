<template>
  <div class="analytic">
    <aside class="analytic-side">
      <h2 class="side-title">解析 · 径向</h2>
      <p class="side-desc">
        solver-analytic {{ SOLVE_SCHEMA_VERSION }} · topology=RF
        <span v-if="projectLabel"> · {{ projectLabel }}</span>
      </p>

      <div class="field">
        <label class="field-label">机型</label>
        <el-radio-group v-model="machineType" size="small" @change="onMachineChange">
          <el-radio-button value="PMSM">PMSM</el-radio-button>
          <el-radio-button value="BLDC">BLDC</el-radio-button>
          <el-radio-button value="ACIM">ACIM</el-radio-button>
        </el-radio-group>
      </div>

      <el-form label-position="top" size="small" class="param-form">
        <h3 class="section-title">geometry</h3>
        <div class="form-grid">
          <el-form-item label="poles">
            <el-input-number v-model="form.geometry.poles" :min="2" :step="2" controls-position="right" />
          </el-form-item>
          <el-form-item label="slots">
            <el-input-number v-model="form.geometry.slots" :min="3" :step="1" controls-position="right" />
          </el-form-item>
          <el-form-item label="stack_length_m">
            <el-input-number v-model="form.geometry.stack_length_m" :min="0.001" :step="0.005" :precision="4" controls-position="right" />
          </el-form-item>
          <el-form-item label="airgap_m">
            <el-input-number v-model="form.geometry.airgap_m" :min="0.0001" :step="0.0001" :precision="5" controls-position="right" />
          </el-form-item>
          <el-form-item label="rotor_od_m">
            <el-input-number v-model="form.geometry.rotor_od_m" :min="0.001" :step="0.005" :precision="4" controls-position="right" />
          </el-form-item>
          <el-form-item label="stator_id_m">
            <el-input-number v-model="form.geometry.stator_id_m" :min="0.001" :step="0.005" :precision="4" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType !== 'ACIM'" label="magnet_thickness_m">
            <el-input-number v-model="form.geometry.magnet_thickness_m" :min="0" :step="0.0005" :precision="4" controls-position="right" />
          </el-form-item>
          <el-form-item label="turns_per_phase">
            <el-input-number v-model="form.geometry.turns_per_phase" :min="1" :step="1" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="rotor_bars">
            <el-input-number v-model="form.geometry.rotor_bars" :min="1" :step="1" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="bar_area_m2">
            <el-input-number v-model="form.geometry.bar_area_m2" :min="1e-8" :step="1e-6" :precision="8" controls-position="right" />
          </el-form-item>
        </div>

        <h3 class="section-title">materials</h3>
        <div class="form-grid">
          <el-form-item label="steel_id">
            <el-select
              v-if="steelOptions.length"
              v-model="form.materials.steel_id"
              filterable
              allow-create
              default-first-option
              placeholder="选择或输入"
              style="width: 100%"
            >
              <el-option v-for="o in steelOptions" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
            <el-input v-else v-model="form.materials.steel_id" />
          </el-form-item>
          <el-form-item v-if="machineType !== 'ACIM'" label="magnet_id">
            <el-select
              v-if="magnetOptions.length"
              v-model="form.materials.magnet_id"
              filterable
              allow-create
              default-first-option
              placeholder="选择或输入"
              style="width: 100%"
            >
              <el-option v-for="o in magnetOptions" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
            <el-input v-else v-model="form.materials.magnet_id" />
          </el-form-item>
          <el-form-item label="conductor_id">
            <el-select
              v-if="coilOptions.length"
              v-model="form.materials.conductor_id"
              filterable
              allow-create
              default-first-option
              placeholder="选择或输入"
              style="width: 100%"
            >
              <el-option v-for="o in coilOptions" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
            <el-input v-else v-model="form.materials.conductor_id" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="bar_id">
            <el-select
              v-if="barOptions.length"
              v-model="form.materials.bar_id"
              filterable
              allow-create
              default-first-option
              placeholder="选择或输入"
              style="width: 100%"
            >
              <el-option v-for="o in barOptions" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
            <el-input v-else v-model="form.materials.bar_id" />
          </el-form-item>
          <el-form-item v-if="machineType !== 'ACIM'" label="br_t">
            <el-input-number v-model="form.materials.br_t" :min="0.1" :max="1.6" :step="0.05" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="sigma_bar">
            <el-input-number v-model="form.materials.sigma_bar" :min="1e5" :step="1e6" :precision="0" controls-position="right" />
          </el-form-item>
        </div>

        <h3 class="section-title">operating_point</h3>
        <div class="form-grid">
          <el-form-item label="speed_rpm">
            <el-input-number v-model="form.operating_point.speed_rpm" :min="0" :step="100" controls-position="right" />
          </el-form-item>
          <el-form-item label="current_a_peak">
            <el-input-number v-model="form.operating_point.current_a_peak" :min="0" :step="1" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'PMSM'" label="gamma_deg">
            <el-input-number v-model="form.operating_point.gamma_deg" :min="-90" :max="90" :step="5" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="slip（可选）">
            <el-input-number v-model="form.operating_point.slip" :min="0.001" :max="0.5" :step="0.01" :precision="3" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="freq_hz">
            <el-input-number v-model="form.operating_point.freq_hz" :min="1" :max="400" :step="1" :precision="1" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="voltage_v_peak">
            <el-input-number v-model="form.operating_point.voltage_v_peak" :min="0" :step="10" controls-position="right" />
          </el-form-item>
        </div>
      </el-form>

      <div class="side-actions">
        <el-button type="primary" :loading="solving" @click="onSolve">求解</el-button>
        <el-button :disabled="solving" @click="resetToSample">恢复样例</el-button>
      </div>
      <p class="side-hint">local-first · Wasm→sync→fixture · 不阻塞 /jobs</p>
      <p v-if="solveBackendLabel" class="side-backend">路径：{{ solveBackendLabel }}</p>
    </aside>

    <section class="analytic-main">
      <div v-if="errorMsg" class="error-box">{{ errorMsg }}</div>

      <div v-if="!result && !errorMsg" class="empty-hint">
        填写参数后点「求解」。默认已填入径向 PMSM 样例，可一键跑。
      </div>

      <template v-if="result">
        <div class="meta-banner" :data-mock="result.meta.mock">
          <span class="meta-pill">path={{ result.meta.source || solveBackend || '—' }}</span>
          <span class="meta-pill">solver={{ result.meta.solver }}</span>
          <span class="meta-pill">mock={{ result.meta.mock }}</span>
          <span class="meta-pill">{{ result.meta.elapsed_ms.toFixed(2) }} ms</span>
          <span v-if="result.meta.note" class="meta-note">{{ result.meta.note }}</span>
        </div>

        <div class="kpi-row">
          <div class="kpi-card">
            <div class="kpi-label">转矩</div>
            <div class="kpi-value">{{ fmt(result.torque_nm, 3) }} <span class="kpi-unit">N·m</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">反电势峰</div>
            <div class="kpi-value">{{ fmt(result.back_emf_v_peak, 2) }} <span class="kpi-unit">V</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">铜耗</div>
            <div class="kpi-value">{{ fmt(result.losses_w.copper, 2) }} <span class="kpi-unit">W</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">铁耗</div>
            <div class="kpi-value">{{ fmt(result.losses_w.iron, 2) }} <span class="kpi-unit">W</span></div>
          </div>
        </div>

        <div class="panels">
          <div class="panel">
            <h3 class="panel-title">损耗 / 电感</h3>
            <el-table :data="lossRows" size="small" stripe empty-text="—" style="width: 100%">
              <el-table-column prop="name" label="项" min-width="120" />
              <el-table-column prop="value" label="数值" min-width="100" />
              <el-table-column prop="unit" label="单位" width="72" />
            </el-table>
          </div>
          <div class="panel chart-panel">
            <div class="chart-header">
              <h3 class="panel-title">转速扫描</h3>
              <el-radio-group v-model="chartMetric" size="small">
                <el-radio-button value="torque">T–n</el-radio-button>
                <el-radio-button value="bemf">E–n</el-radio-button>
              </el-radio-group>
            </div>
            <div ref="chartEl" class="chart" />
            <p v-if="sweepError" class="sweep-error">{{ sweepError }}</p>
          </div>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ECharts } from 'echarts/core'
import {
  DEFAULT_RADIAL_ACIM_REQUEST,
  DEFAULT_RADIAL_PMSM_REQUEST,
  SOLVE_SCHEMA_VERSION,
  type MachineType,
  type SolveBackend,
  type SolveRequest,
  type SolveResult,
  type SweepPoint,
} from '@/types/solver'
import {
  defaultSpeedSweep,
  getSolveBackend,
  solveRadial,
  sweepSpeed,
} from '@/lib/analyticSolve'
import { listMaterials } from '@/api/materials'
import { useProjectsStore } from '@/stores/projects'

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const route = useRoute()
const projects = useProjectsStore()

const machineType = ref<MachineType>('PMSM')
const form = ref(cloneRequest(DEFAULT_RADIAL_PMSM_REQUEST))
const solving = ref(false)
const result = ref<SolveResult | null>(null)
const errorMsg = ref<string | null>(null)
const sweepPoints = ref<SweepPoint[]>([])
const sweepError = ref<string | null>(null)
const chartMetric = ref<'torque' | 'bemf'>('torque')
const chartEl = ref<HTMLDivElement | null>(null)
const solveBackend = ref<SolveBackend | null>(null)
const steelOptions = ref<{ id: string; label: string }[]>([])
const magnetOptions = ref<{ id: string; label: string }[]>([])
const coilOptions = ref<{ id: string; label: string }[]>([])
const barOptions = ref<{ id: string; label: string }[]>([])
let chart: ECharts | null = null

const BACKEND_LABELS: Record<SolveBackend, string> = {
  wasm: 'Wasm',
  sync: 'sync HTTP',
  fixture: 'fixture',
  mock: 'mock',
}

const solveBackendLabel = computed(() => {
  const b = result.value?.meta.source ?? solveBackend.value
  return b ? BACKEND_LABELS[b] ?? b : ''
})

const projectLabel = computed(() => {
  const id = typeof route.query.projectId === 'string' ? route.query.projectId : ''
  if (!id) return ''
  const p = projects.items.find((x) => x.id === id)
  return p ? `${p.name} (${id})` : `projectId=${id}`
})

const lossRows = computed(() => {
  const r = result.value
  if (!r) return []
  const rows: { name: string; value: string; unit: string }[] = [
    { name: 'copper', value: fmt(r.losses_w.copper, 3), unit: 'W' },
    { name: 'iron', value: fmt(r.losses_w.iron, 3), unit: 'W' },
  ]
  if (r.losses_w.magnet_eddy != null) {
    rows.push({ name: 'magnet_eddy', value: fmt(r.losses_w.magnet_eddy, 4), unit: 'W' })
  }
  if (r.losses_w.rotor_bar != null) {
    rows.push({ name: 'rotor_bar', value: fmt(r.losses_w.rotor_bar, 3), unit: 'W' })
  }
  if (r.inductance_h?.ld != null) {
    rows.push({ name: 'Ld', value: fmt(r.inductance_h.ld * 1e3, 4), unit: 'mH' })
  }
  if (r.inductance_h?.lq != null) {
    rows.push({ name: 'Lq', value: fmt(r.inductance_h.lq * 1e3, 4), unit: 'mH' })
  }
  return rows
})

function fmt(n: number, digits: number): string {
  if (!Number.isFinite(n)) return '—'
  return n.toFixed(digits)
}

function cloneRequest(src: SolveRequest): SolveRequest {
  return {
    schema_version: SOLVE_SCHEMA_VERSION,
    topology: 'RF',
    machine_type: src.machine_type,
    geometry: { ...src.geometry },
    materials: { ...src.materials },
    operating_point: { ...src.operating_point },
  }
}

function resetToSample() {
  if (machineType.value === 'ACIM') {
    form.value = cloneRequest(DEFAULT_RADIAL_ACIM_REQUEST)
  } else {
    const base = cloneRequest(DEFAULT_RADIAL_PMSM_REQUEST)
    base.machine_type = machineType.value
    if (machineType.value === 'BLDC') {
      delete base.operating_point.gamma_deg
      delete base.operating_point.slip
      delete base.operating_point.voltage_v_peak
      delete base.operating_point.freq_hz
    } else {
      delete base.operating_point.slip
      delete base.operating_point.voltage_v_peak
      delete base.operating_point.freq_hz
      base.operating_point.gamma_deg = 0
    }
    form.value = base
  }
  result.value = null
  sweepPoints.value = []
  errorMsg.value = null
  sweepError.value = null
  solveBackend.value = null
}

function onMachineChange() {
  resetToSample()
}

function buildRequest(): SolveRequest {
  const f = form.value
  return {
    schema_version: SOLVE_SCHEMA_VERSION,
    topology: 'RF',
    machine_type: machineType.value,
    geometry: { ...f.geometry },
    materials: { ...f.materials },
    operating_point: { ...f.operating_point },
  }
}

async function onSolve() {
  solving.value = true
  errorMsg.value = null
  sweepError.value = null
  try {
    const req = buildRequest()
    const r = await solveRadial(req)
    result.value = r
    solveBackend.value = getSolveBackend()
    await nextTick()
    ensureChart()
    try {
      const speeds = defaultSpeedSweep(req.operating_point.speed_rpm)
      sweepPoints.value = await sweepSpeed(req, speeds)
      renderChart()
    } catch (e) {
      sweepPoints.value = []
      sweepError.value = e instanceof Error ? e.message : String(e)
    }
  } catch (e) {
    result.value = null
    sweepPoints.value = []
    errorMsg.value = e instanceof Error ? e.message : String(e)
  } finally {
    solving.value = false
  }
}

function ensureChart() {
  if (!chartEl.value) return
  if (!chart) {
    chart = echarts.init(chartEl.value, undefined, { renderer: 'canvas' })
  }
}

function renderChart() {
  ensureChart()
  if (!chart) return
  const pts = sweepPoints.value
  const xs = pts.map((p) => p.speed_rpm)
  const isT = chartMetric.value === 'torque'
  const ys = pts.map((p) => (isT ? p.torque_nm : p.back_emf_v_peak))
  chart.setOption(
    {
      backgroundColor: 'transparent',
      grid: { left: 48, right: 16, top: 28, bottom: 36 },
      tooltip: { trigger: 'axis' },
      legend: {
        data: [isT ? '转矩 T' : '反电势 E'],
        textStyle: { color: '#9aa0a6', fontSize: 11 },
        top: 0,
      },
      xAxis: {
        type: 'category',
        data: xs,
        name: 'rpm',
        nameTextStyle: { color: '#6b7280' },
        axisLabel: { color: '#9aa0a6' },
        axisLine: { lineStyle: { color: '#2a2d34' } },
      },
      yAxis: {
        type: 'value',
        name: isT ? 'N·m' : 'V',
        nameTextStyle: { color: '#6b7280' },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { lineStyle: { color: '#1f2228' } },
        axisLine: { lineStyle: { color: '#2a2d34' } },
      },
      series: [
        {
          name: isT ? '转矩 T' : '反电势 E',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          data: ys,
          lineStyle: { color: isT ? '#2dd4bf' : '#f59e0b', width: 2 },
          itemStyle: { color: isT ? '#2dd4bf' : '#f59e0b' },
          areaStyle: {
            color: isT ? 'rgba(45,212,191,0.12)' : 'rgba(245,158,11,0.12)',
          },
        },
      ],
    },
    true,
  )
}

function onResize() {
  chart?.resize()
}

watch(chartMetric, () => {
  if (sweepPoints.value.length) renderChart()
})

async function loadMaterialOptions() {
  try {
    const { items } = await listMaterials()
    steelOptions.value = items
      .filter((m) => m.category === 'steel')
      .map((m) => ({ id: m.id, label: `${m.name} (${m.id})` }))
    magnetOptions.value = items
      .filter((m) => m.category === 'magnet')
      .map((m) => ({ id: m.id, label: `${m.name} (${m.id})` }))
    coilOptions.value = items
      .filter((m) => m.category === 'coil')
      .map((m) => ({ id: m.id, label: `${m.name} (${m.id})` }))
    barOptions.value = items
      .filter((m) => m.category === 'acim_bar')
      .map((m) => ({ id: m.id, label: `${m.name} (${m.id})` }))
  } catch {
    /* listMaterials 失败则保持手填 id */
    steelOptions.value = []
    magnetOptions.value = []
    coilOptions.value = []
    barOptions.value = []
  }
}

onMounted(async () => {
  const id = typeof route.query.projectId === 'string' ? route.query.projectId : ''
  if (id && !projects.items.length) {
    try {
      await projects.fetchProjects()
    } catch {
      /* optional label only */
    }
  }
  void loadMaterialOptions()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.analytic {
  display: flex;
  height: 100%;
  min-height: 0;
}

.analytic-side {
  width: 320px;
  flex-shrink: 0;
  padding: 16px;
  border-right: 1px solid var(--mo-border);
  background: var(--mo-bg-panel);
  overflow: auto;
}

.side-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
}

.side-desc {
  margin: 0 0 12px;
  font-size: 11px;
  color: var(--mo-text-muted);
  font-family: var(--mo-font-mono);
}

.field {
  margin-bottom: 12px;
}

.field-label {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  color: var(--mo-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.section-title {
  margin: 12px 0 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--mo-accent);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.param-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.param-form :deep(.el-input-number) {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 8px;
}

.side-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.side-hint {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--mo-text-muted);
}

.side-backend {
  margin: 4px 0 0;
  font-size: 11px;
  font-family: var(--mo-font-mono);
  color: var(--mo-accent);
}

.analytic-main {
  flex: 1;
  min-width: 0;
  padding: 16px 20px;
  overflow: auto;
}

.empty-hint {
  color: var(--mo-text-secondary);
  padding: 48px 0;
  text-align: center;
}

.error-box {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: var(--mo-radius);
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.35);
  color: #fca5a5;
  font-family: var(--mo-font-mono);
  font-size: 12px;
  white-space: pre-wrap;
}

.meta-banner {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: baseline;
  margin-bottom: 14px;
  padding: 8px 10px;
  border-radius: var(--mo-radius);
  background: var(--mo-bg-elevated);
  border: 1px solid var(--mo-border);
}

.meta-banner[data-mock='true'] {
  border-color: rgba(245, 158, 11, 0.45);
}

.meta-pill {
  font-family: var(--mo-font-mono);
  font-size: 11px;
  color: var(--mo-accent);
  background: var(--mo-accent-dim);
  padding: 2px 6px;
  border-radius: var(--mo-radius-sm);
}

.meta-note {
  flex: 1 1 100%;
  font-size: 11px;
  color: var(--mo-text-secondary);
  line-height: 1.4;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.kpi-card {
  padding: 12px 14px;
  background: var(--mo-bg-elevated);
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius);
}

.kpi-label {
  font-size: 11px;
  color: var(--mo-text-muted);
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 20px;
  font-weight: 600;
  font-family: var(--mo-font-mono);
  color: var(--mo-text-primary);
}

.kpi-unit {
  font-size: 12px;
  font-weight: 400;
  color: var(--mo-text-muted);
}

.panels {
  display: grid;
  grid-template-columns: minmax(240px, 340px) 1fr;
  gap: 12px;
  align-items: stretch;
}

.panel {
  background: var(--mo-bg-panel);
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius);
  padding: 12px;
}

.panel-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.chart-header .panel-title {
  margin: 0;
}

.chart {
  width: 100%;
  height: 320px;
}

.sweep-error {
  margin: 6px 0 0;
  font-size: 11px;
  color: #fca5a5;
}

@media (max-width: 960px) {
  .analytic {
    flex-direction: column;
  }
  .analytic-side {
    width: 100%;
    max-height: 42vh;
    border-right: none;
    border-bottom: 1px solid var(--mo-border);
  }
  .kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .panels {
    grid-template-columns: 1fr;
  }
}
</style>
