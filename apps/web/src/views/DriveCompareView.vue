<template>
  <div class="compare">
    <aside class="compare-side">
      <h2 class="side-title">驱动对比 · Q4</h2>
      <p class="side-desc">fixture samples · source=drive</p>

      <div class="field">
        <label class="field-label">对比组</label>
        <el-radio-group v-model="family" size="small" @change="onFamilyChange">
          <el-radio-button value="pm">永磁</el-radio-button>
          <el-radio-button value="acim">ACIM</el-radio-button>
        </el-radio-group>
      </div>

      <div class="pair-meta">
        <div class="pair-row">
          <span class="pair-tag tag-a">A</span>
          <span>{{ pair.a.label }}</span>
        </div>
        <code class="pair-path">{{ pair.a.path }}</code>
        <div class="pair-row" style="margin-top: 8px">
          <span class="pair-tag tag-b">B</span>
          <span>{{ pair.b.label }}</span>
        </div>
        <code class="pair-path">{{ pair.b.path }}</code>
      </div>

      <div class="side-actions">
        <el-button size="small" :loading="loading" @click="loadPair">重新加载样例</el-button>
        <el-button size="small" type="primary" :disabled="!sideA || !sideB" @click="exportJson">
          导出 JSON
        </el-button>
        <el-button size="small" type="success" :disabled="!sideA || !sideB" @click="exportCsv">
          导出 CSV
        </el-button>
      </div>
      <p class="side-hint">默认加载 public 样例；不宣称 ≤3%/≤5% 等指标。</p>
    </aside>

    <section class="compare-main">
      <div class="meta-banner">
        <span class="meta-pill">驱动样例 · source=drive</span>
        <span class="meta-pill">{{ pair.label }}</span>
        <span v-if="sideA?._samplePath" class="meta-note">
          A={{ sideA._samplePath }} · B={{ sideB?._samplePath }}
        </span>
      </div>

      <div v-if="errorMsg" class="error-box">{{ errorMsg }}</div>
      <div v-if="loading && !sideA" class="empty-hint">加载样例中…</div>

      <template v-if="sideA && sideB">
        <div class="dual-kpis">
          <div class="summary-card card-a">
            <div class="summary-head">
              <span class="pair-tag tag-a">A</span>
              <strong>{{ pair.a.label }}</strong>
              <span class="mode-chip">{{ sideA.mode }}</span>
            </div>
            <div class="kpi-grid">
              <div class="kpi">
                <div class="kpi-label">平均转矩</div>
                <div class="kpi-value">
                  {{ fmt(sideA.metrics?.torqueAvgNm, 3) }}
                  <span class="kpi-unit">N·m</span>
                </div>
              </div>
              <div class="kpi">
                <div class="kpi-label">脉动峰峰</div>
                <div class="kpi-value">
                  {{ fmt(rippleOf(sideA), 3) }}
                  <span class="kpi-unit">N·m</span>
                </div>
              </div>
              <div class="kpi">
                <div class="kpi-label">效率</div>
                <div class="kpi-value">{{ fmtPct(sideA.metrics?.efficiency) }}</div>
              </div>
              <div class="kpi">
                <div class="kpi-label">损耗合计</div>
                <div class="kpi-value">
                  {{ fmt(lossesTotal(sideA.lossesW), 2) }}
                  <span class="kpi-unit">W</span>
                </div>
              </div>
            </div>
          </div>

          <div class="summary-card card-b">
            <div class="summary-head">
              <span class="pair-tag tag-b">B</span>
              <strong>{{ pair.b.label }}</strong>
              <span class="mode-chip">{{ sideB.mode }}</span>
            </div>
            <div class="kpi-grid">
              <div class="kpi">
                <div class="kpi-label">平均转矩</div>
                <div class="kpi-value">
                  {{ fmt(sideB.metrics?.torqueAvgNm, 3) }}
                  <span class="kpi-unit">N·m</span>
                </div>
              </div>
              <div class="kpi">
                <div class="kpi-label">脉动峰峰</div>
                <div class="kpi-value">
                  {{ fmt(rippleOf(sideB), 3) }}
                  <span class="kpi-unit">N·m</span>
                </div>
              </div>
              <div class="kpi">
                <div class="kpi-label">效率</div>
                <div class="kpi-value">{{ fmtPct(sideB.metrics?.efficiency) }}</div>
              </div>
              <div class="kpi">
                <div class="kpi-label">损耗合计</div>
                <div class="kpi-value">
                  {{ fmt(lossesTotal(sideB.lossesW), 2) }}
                  <span class="kpi-unit">W</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="panels">
          <div class="panel chart-panel">
            <h3 class="panel-title">转矩波形 overlay · torque_nm vs t_s</h3>
            <div ref="torqueChartEl" class="chart-box" />
          </div>
          <div class="panel chart-panel">
            <h3 class="panel-title">损耗分量 · lossesW</h3>
            <div ref="lossChartEl" class="chart-box" />
          </div>
        </div>

        <div class="panel" style="margin-top: 12px">
          <h3 class="panel-title">指标对比 A / B / Δ</h3>
          <el-table :data="metricRows" size="small" stripe style="width: 100%">
            <el-table-column prop="name" label="指标" min-width="140" />
            <el-table-column prop="a" :label="'A · ' + pair.a.label" min-width="120" />
            <el-table-column prop="b" :label="'B · ' + pair.b.label" min-width="120" />
            <el-table-column prop="delta" label="Δ (B−A)" min-width="120" />
            <el-table-column prop="unit" label="单位" width="80" />
          </el-table>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ECharts } from 'echarts/core'
import {
  COMPARE_PAIRS,
  LOSS_KEYS,
  lossesTotal,
  ripplePp,
  type CompareFamily,
  type DriveSampleResult,
} from '@/types/driveCompare'

echarts.use([
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
])

const family = ref<CompareFamily>('pm')
const loading = ref(false)
const errorMsg = ref('')
const sideA = ref<DriveSampleResult | null>(null)
const sideB = ref<DriveSampleResult | null>(null)

const torqueChartEl = ref<HTMLDivElement | null>(null)
const lossChartEl = ref<HTMLDivElement | null>(null)
let torqueChart: ECharts | null = null
let lossChart: ECharts | null = null

const pair = computed(() => COMPARE_PAIRS[family.value])

function fmt(v: unknown, dig = 2): string {
  if (v == null || typeof v !== 'number' || Number.isNaN(v)) return '—'
  return v.toFixed(dig)
}

function fmtPct(v: unknown): string {
  if (v == null || typeof v !== 'number' || Number.isNaN(v)) return '—'
  return `${(v * 100).toFixed(1)}%`
}

function rippleOf(s: DriveSampleResult | null): number | null {
  return ripplePp(s?.metrics)
}

function numOrNull(v: unknown): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}

function deltaStr(a: number | null, b: number | null, dig = 3): string {
  if (a == null || b == null) return '—'
  const d = b - a
  const sign = d > 0 ? '+' : ''
  return `${sign}${d.toFixed(dig)}`
}

const metricRows = computed(() => {
  const a = sideA.value
  const b = sideB.value
  if (!a || !b) return []

  const rows: { name: string; a: string; b: string; delta: string; unit: string }[] = []

  const tA = numOrNull(a.metrics?.torqueAvgNm)
  const tB = numOrNull(b.metrics?.torqueAvgNm)
  rows.push({
    name: 'torqueAvgNm',
    a: fmt(tA, 3),
    b: fmt(tB, 3),
    delta: deltaStr(tA, tB, 3),
    unit: 'N·m',
  })

  const rA = rippleOf(a)
  const rB = rippleOf(b)
  rows.push({
    name: 'torqueRipplePpNm',
    a: fmt(rA, 3),
    b: fmt(rB, 3),
    delta: deltaStr(rA, rB, 3),
    unit: 'N·m',
  })

  const eA = numOrNull(a.metrics?.efficiency)
  const eB = numOrNull(b.metrics?.efficiency)
  rows.push({
    name: 'efficiency',
    a: fmtPct(eA),
    b: fmtPct(eB),
    delta:
      eA == null || eB == null
        ? '—'
        : `${(eB - eA > 0 ? '+' : '')}${((eB - eA) * 100).toFixed(2)} pp`,
    unit: '',
  })

  const pMechA = numOrNull(a.metrics?.pMechW)
  const pMechB = numOrNull(b.metrics?.pMechW)
  rows.push({
    name: 'pMechW',
    a: fmt(pMechA, 2),
    b: fmt(pMechB, 2),
    delta: deltaStr(pMechA, pMechB, 2),
    unit: 'W',
  })

  const pElecA = numOrNull(a.metrics?.pElecW)
  const pElecB = numOrNull(b.metrics?.pElecW)
  rows.push({
    name: 'pElecW',
    a: fmt(pElecA, 2),
    b: fmt(pElecB, 2),
    delta: deltaStr(pElecA, pElecB, 2),
    unit: 'W',
  })

  const lossA = lossesTotal(a.lossesW)
  const lossB = lossesTotal(b.lossesW)
  rows.push({
    name: 'lossesW total',
    a: fmt(lossA, 2),
    b: fmt(lossB, 2),
    delta: deltaStr(lossA, lossB, 2),
    unit: 'W',
  })

  for (const k of LOSS_KEYS) {
    const la = numOrNull(a.lossesW?.[k])
    const lb = numOrNull(b.lossesW?.[k])
    rows.push({
      name: `lossesW.${k}`,
      a: fmt(la, 3),
      b: fmt(lb, 3),
      delta: deltaStr(la, lb, 3),
      unit: 'W',
    })
  }

  const iA = numOrNull(a.currentsA?.rmsPhase)
  const iB = numOrNull(b.currentsA?.rmsPhase)
  rows.push({
    name: 'currentsA.rmsPhase',
    a: fmt(iA, 3),
    b: fmt(iB, 3),
    delta: deltaStr(iA, iB, 3),
    unit: 'A',
  })

  return rows
})

async function fetchSample(path: string): Promise<DriveSampleResult> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`加载失败 ${path}: HTTP ${res.status}`)
  const data = (await res.json()) as DriveSampleResult
  data._samplePath = path
  return data
}

async function loadPair() {
  loading.value = true
  errorMsg.value = ''
  try {
    const p = pair.value
    const [a, b] = await Promise.all([fetchSample(p.a.path), fetchSample(p.b.path)])
    sideA.value = a
    sideB.value = b
    await nextTick()
    renderCharts()
  } catch (e: unknown) {
    sideA.value = null
    sideB.value = null
    errorMsg.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function onFamilyChange() {
  void loadPair()
}

function ensureCharts() {
  if (torqueChartEl.value && !torqueChart) {
    torqueChart = echarts.init(torqueChartEl.value, undefined, { renderer: 'canvas' })
  }
  if (lossChartEl.value && !lossChart) {
    lossChart = echarts.init(lossChartEl.value, undefined, { renderer: 'canvas' })
  }
}

function renderCharts() {
  ensureCharts()
  renderTorqueChart()
  renderLossChart()
}

function renderTorqueChart() {
  if (!torqueChart || !sideA.value || !sideB.value) return
  const wa = sideA.value.waveforms
  const wb = sideB.value.waveforms
  const seriesA =
    wa?.t_s && wa?.torque_nm
      ? wa.t_s.map((t, i) => [t, wa.torque_nm[i] ?? null])
      : []
  const seriesB =
    wb?.t_s && wb?.torque_nm
      ? wb.t_s.map((t, i) => [t, wb.torque_nm[i] ?? null])
      : []

  torqueChart.setOption(
    {
      backgroundColor: 'transparent',
      grid: { left: 52, right: 16, top: 36, bottom: 40 },
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v: unknown) =>
          typeof v === 'number' ? v.toFixed(4) : String(v ?? ''),
      },
      legend: {
        data: [pair.value.a.label, pair.value.b.label],
        textStyle: { color: '#9aa0a6', fontSize: 11 },
        top: 0,
      },
      xAxis: {
        type: 'value',
        name: 't_s',
        nameTextStyle: { color: '#6b7280' },
        axisLabel: { color: '#9aa0a6', formatter: (v: number) => v.toExponential(1) },
        axisLine: { lineStyle: { color: '#2a2d34' } },
        splitLine: { lineStyle: { color: '#1f2228' } },
      },
      yAxis: {
        type: 'value',
        name: 'N·m',
        nameTextStyle: { color: '#6b7280' },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { lineStyle: { color: '#1f2228' } },
        axisLine: { lineStyle: { color: '#2a2d34' } },
      },
      series: [
        {
          name: pair.value.a.label,
          type: 'line',
          showSymbol: false,
          data: seriesA,
          lineStyle: { color: '#38bdf8', width: 1.5 },
          itemStyle: { color: '#38bdf8' },
        },
        {
          name: pair.value.b.label,
          type: 'line',
          showSymbol: false,
          data: seriesB,
          lineStyle: { color: '#fbbf24', width: 1.5 },
          itemStyle: { color: '#fbbf24' },
        },
      ],
    },
    true,
  )
}

function renderLossChart() {
  if (!lossChart || !sideA.value || !sideB.value) return
  const cats = [...LOSS_KEYS]
  const aVals = cats.map((k) => {
    const v = sideA.value?.lossesW?.[k]
    return typeof v === 'number' && Number.isFinite(v) ? v : 0
  })
  const bVals = cats.map((k) => {
    const v = sideB.value?.lossesW?.[k]
    return typeof v === 'number' && Number.isFinite(v) ? v : 0
  })

  lossChart.setOption(
    {
      backgroundColor: 'transparent',
      grid: { left: 52, right: 16, top: 36, bottom: 40 },
      tooltip: { trigger: 'axis' },
      legend: {
        data: [pair.value.a.label, pair.value.b.label],
        textStyle: { color: '#9aa0a6', fontSize: 11 },
        top: 0,
      },
      xAxis: {
        type: 'category',
        data: cats,
        axisLabel: { color: '#9aa0a6', fontSize: 11 },
        axisLine: { lineStyle: { color: '#2a2d34' } },
      },
      yAxis: {
        type: 'value',
        name: 'W',
        nameTextStyle: { color: '#6b7280' },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { lineStyle: { color: '#1f2228' } },
        axisLine: { lineStyle: { color: '#2a2d34' } },
      },
      series: [
        {
          name: pair.value.a.label,
          type: 'bar',
          data: aVals,
          itemStyle: { color: '#38bdf8' },
          barGap: '20%',
        },
        {
          name: pair.value.b.label,
          type: 'bar',
          data: bVals,
          itemStyle: { color: '#fbbf24' },
        },
      ],
    },
    true,
  )
}

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function exportJson() {
  if (!sideA.value || !sideB.value) return
  const payload = {
    family: family.value,
    label: pair.value.label,
    source: 'drive',
    banner: '驱动样例 · source=drive',
    a: { label: pair.value.a.label, path: pair.value.a.path, result: sideA.value },
    b: { label: pair.value.b.label, path: pair.value.b.path, result: sideB.value },
    exportedAt: new Date().toISOString(),
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  downloadBlob(`drive-compare-${family.value}.json`, blob)
}

function exportCsv() {
  if (!sideA.value || !sideB.value) return
  const lines = ['name,A,B,delta,unit']
  for (const r of metricRows.value) {
    const esc = (s: string) => `"${s.replace(/"/g, '""')}"`
    lines.push([esc(r.name), esc(r.a), esc(r.b), esc(r.delta), esc(r.unit)].join(','))
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  downloadBlob(`drive-compare-${family.value}-metrics.csv`, blob)
}

function onResize() {
  torqueChart?.resize()
  lossChart?.resize()
}

watch([sideA, sideB], async () => {
  await nextTick()
  renderCharts()
})

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await loadPair()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  torqueChart?.dispose()
  lossChart?.dispose()
  torqueChart = null
  lossChart = null
})
</script>

<style scoped>
.compare {
  display: flex;
  height: 100%;
  min-height: 0;
}
.compare-side {
  width: 300px;
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
.pair-meta {
  margin: 12px 0;
  padding: 10px;
  border-radius: var(--mo-radius);
  background: var(--mo-bg-elevated);
  border: 1px solid var(--mo-border);
}
.pair-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.pair-path {
  display: block;
  margin-top: 2px;
  margin-left: 28px;
  font-size: 10px;
  color: var(--mo-text-muted);
  word-break: break-all;
}
.pair-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  font-family: var(--mo-font-mono);
}
.tag-a {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
}
.tag-b {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}
.side-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}
.side-hint {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--mo-text-muted);
}
.compare-main {
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
  font-family: var(--mo-font-mono);
}
.dual-kpis {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
}
.summary-card {
  padding: 12px 14px;
  background: var(--mo-bg-elevated);
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius);
}
.card-a {
  border-top: 2px solid #38bdf8;
}
.card-b {
  border-top: 2px solid #fbbf24;
}
.summary-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
}
.mode-chip {
  margin-left: auto;
  font-family: var(--mo-font-mono);
  font-size: 11px;
  color: var(--mo-text-muted);
}
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.kpi-label {
  font-size: 11px;
  color: var(--mo-text-muted);
  margin-bottom: 2px;
}
.kpi-value {
  font-size: 18px;
  font-weight: 600;
  font-family: var(--mo-font-mono);
}
.kpi-unit {
  font-size: 11px;
  font-weight: 400;
  color: var(--mo-text-muted);
}
.panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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
.chart-box {
  width: 100%;
  height: 280px;
  background: var(--mo-bg-elevated);
  border-radius: var(--mo-radius-sm);
}
@media (max-width: 960px) {
  .compare {
    flex-direction: column;
  }
  .compare-side {
    width: 100%;
    max-height: 36vh;
    border-right: none;
    border-bottom: 1px solid var(--mo-border);
  }
  .dual-kpis,
  .panels {
    grid-template-columns: 1fr;
  }
}
</style>
