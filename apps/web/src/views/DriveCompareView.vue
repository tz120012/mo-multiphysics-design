<template>
  <div class="compare">
    <header class="compare-toolbar">
      <div>
        <h2 class="title">同屏对比</h2>
        <p class="desc">驱动模式的转矩脉动与损耗分离</p>
      </div>
      <el-radio-group v-model="scheme" size="small">
        <el-radio-button value="pm">永磁（方波 vs FOC）</el-radio-button>
        <el-radio-button value="acim">ACIM（V/f vs FOC）</el-radio-button>
      </el-radio-group>
      <div class="toolbar-actions">
        <el-button :disabled="!left || !right || loading" @click="exportJson">导出 JSON</el-button>
        <el-button :disabled="!left || !right || loading" @click="exportCsv">导出 CSV</el-button>
      </div>
    </header>

    <div v-if="left && right" class="fixture-banner" role="status">source=drive 样例</div>
    <div v-if="errorMsg" class="error-box">{{ errorMsg }}</div>

    <div v-loading="loading" class="compare-body">
      <template v-if="left && right">
        <p class="scheme">
          <span>A · {{ labelOf(left) }}</span>
          <span class="pill">{{ left.machineType }}</span>
          <span>B · {{ labelOf(right) }}</span>
          <span class="pill">{{ right.machineType }}</span>
        </p>

        <div class="card-row">
          <article v-for="side in sides" :key="side.tag" class="summary-card" :data-side="side.tag">
            <header class="card-head">
              <span class="side-tag">{{ side.tag }}</span>
              <div>
                <h3>{{ labelOf(side.item) }}</h3>
                <p>
                  {{ side.item.machineType }}
                  · {{ fmt(num(side.item.operatingPoint?.speedRpm), 0) }} rpm
                </p>
              </div>
            </header>
            <dl class="kpi-grid">
              <div>
                <dt>平均转矩</dt>
                <dd>{{ fmt(num(side.item.metrics?.torqueAvgNm), 4) }}<span>N·m</span></dd>
              </div>
              <div>
                <dt>脉动峰峰</dt>
                <dd>{{ fmt(ripplePp(side.item.metrics), 4) }}<span>N·m</span></dd>
              </div>
              <div>
                <dt>效率 η</dt>
                <dd>{{ fmt(num(side.item.metrics?.efficiency), 2, true) }}<span>%</span></dd>
              </div>
              <div>
                <dt>总损耗</dt>
                <dd>{{ fmt(lossTotal(side.item.lossesW), 2) }}<span>W</span></dd>
              </div>
            </dl>
          </article>
        </div>

        <div class="chart-grid">
          <section class="panel">
            <div class="panel-head">
              <h3>转矩波形</h3>
              <span class="panel-unit">t / ms · N·m</span>
            </div>
            <div ref="torqueEl" class="chart" />
          </section>
          <section class="panel">
            <div class="panel-head">
              <h3>损耗分离</h3>
              <span class="panel-unit">lossesW · W</span>
            </div>
            <div ref="lossEl" class="chart" />
          </section>
        </div>

        <section class="panel">
          <div class="panel-head">
            <h3>指标对照</h3>
            <span class="panel-unit">Δ = A − B · 效率为百分数</span>
          </div>
          <el-table :data="tableRows" size="small" stripe empty-text="—" class="metrics-table">
            <el-table-column prop="metric" label="指标" min-width="120" />
            <el-table-column prop="unit" label="单位" width="72" />
            <el-table-column prop="a" :label="colA" min-width="120" />
            <el-table-column prop="b" :label="colB" min-width="120" />
            <el-table-column prop="delta" label="Δ (A−B)" min-width="110" />
          </el-table>
        </section>
      </template>
      <p v-else-if="!loading && !errorMsg" class="empty-hint">正在等待样例。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ECharts } from 'echarts/core'
import type { DriveCaseResult } from '@/api/types'
import {
  COMPARE_URLS,
  DRIVE_MODE_LABEL,
  LOSS_KEYS,
  LOSS_LABEL,
  compareCsv,
  compareRows,
  formatDelta,
  formatNum,
  lossOf,
  lossTotal,
  num,
  parseDriveCase,
  ripplePp,
  type CompareScheme,
  type LossKey,
} from '@/lib/driveCompare'

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const CASE_COLOR = ['#2dd4bf', '#f59e0b']
const LOSS_COLOR: Record<LossKey, string> = {
  copper: '#f59e0b',
  iron: '#2dd4bf',
  magnetEddy: '#a78bfa',
  bar: '#60a5fa',
  endRing: '#fb7185',
}

const scheme = ref<CompareScheme>('pm')
const loading = ref(true)
const errorMsg = ref('')
const left = ref<DriveCaseResult | null>(null)
const right = ref<DriveCaseResult | null>(null)
const rawPair = ref<unknown[] | null>(null)
const torqueEl = ref<HTMLDivElement | null>(null)
const lossEl = ref<HTMLDivElement | null>(null)
let torqueChart: ECharts | null = null
let lossChart: ECharts | null = null
let loadSeq = 0

const sides = computed(() => {
  if (!left.value || !right.value) return []
  return [
    { tag: 'A', item: left.value },
    { tag: 'B', item: right.value },
  ]
})

const colA = computed(() => (left.value ? `A · ${labelOf(left.value)}` : 'A'))
const colB = computed(() => (right.value ? `B · ${labelOf(right.value)}` : 'B'))

const tableRows = computed(() => {
  if (!left.value || !right.value) return []
  return compareRows(left.value, right.value).map((r) => {
    const pct = r.asPercent === true
    return {
      metric: r.label,
      unit: pct ? '%' : r.unit,
      a: formatNum(r.a, r.digits, pct),
      b: formatNum(r.b, r.digits, pct),
      delta: formatDelta(r.a, r.b, r.digits, pct),
    }
  })
})

function labelOf(item: DriveCaseResult): string {
  return DRIVE_MODE_LABEL[item.mode ?? ''] ?? item.mode ?? '—'
}

function fmt(v: number | null, digits: number, asPercent = false): string {
  return formatNum(v, digits, asPercent)
}

function tooltip() {
  return {
    trigger: 'axis' as const,
    backgroundColor: '#1a1c21',
    borderColor: '#2a2d34',
    textStyle: { color: '#e8eaed', fontSize: 12 },
  }
}

function renderCharts() {
  if (!left.value || !right.value || !torqueEl.value || !lossEl.value) return
  const pair = [left.value, right.value]
  if (!torqueChart || torqueChart.isDisposed()) {
    torqueChart = echarts.init(torqueEl.value, undefined, { renderer: 'canvas' })
  }
  torqueChart.setOption(
    {
      backgroundColor: 'transparent',
      grid: { left: 52, right: 16, top: 32, bottom: 32 },
      tooltip: tooltip(),
      legend: {
        data: pair.map((item) => labelOf(item)),
        textStyle: { color: '#9aa0a6', fontSize: 11 },
        top: 0,
      },
      xAxis: {
        type: 'value',
        name: 'ms',
        nameTextStyle: { color: '#6b7280' },
        axisLabel: { color: '#9aa0a6' },
        axisLine: { lineStyle: { color: '#2a2d34' } },
        splitLine: { lineStyle: { color: '#1f2228' } },
      },
      yAxis: {
        type: 'value',
        name: 'N·m',
        scale: true,
        nameTextStyle: { color: '#6b7280' },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { lineStyle: { color: '#1f2228' } },
      },
      series: pair.map((item, index) => ({
        name: labelOf(item),
        type: 'line' as const,
        showSymbol: false,
        data: (item.waveforms?.t_s ?? []).map((t, i) => [t * 1e3, item.waveforms?.torque_nm[i]]),
        lineStyle: { width: 1.6, color: CASE_COLOR[index] },
        itemStyle: { color: CASE_COLOR[index] },
      })),
    },
    true,
  )

  const keys = LOSS_KEYS.filter((key) => lossOf(left.value?.lossesW, key) != null || lossOf(right.value?.lossesW, key) != null)
  if (!lossChart || lossChart.isDisposed()) {
    lossChart = echarts.init(lossEl.value, undefined, { renderer: 'canvas' })
  }
  lossChart.setOption(
    {
      backgroundColor: 'transparent',
      grid: { left: 52, right: 16, top: 36, bottom: 32 },
      tooltip: tooltip(),
      legend: {
        data: keys.map((key) => LOSS_LABEL[key]),
        textStyle: { color: '#9aa0a6', fontSize: 11 },
        top: 0,
      },
      xAxis: {
        type: 'category',
        data: pair.map((item, index) => `${index === 0 ? 'A' : 'B'} · ${labelOf(item)}`),
        axisLabel: { color: '#9aa0a6', interval: 0 },
        axisLine: { lineStyle: { color: '#2a2d34' } },
      },
      yAxis: {
        type: 'value',
        name: 'W',
        min: 0,
        nameTextStyle: { color: '#6b7280' },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { lineStyle: { color: '#1f2228' } },
      },
      series: keys.map((key) => ({
        name: LOSS_LABEL[key],
        type: 'bar' as const,
        stack: 'losses',
        barMaxWidth: 64,
        data: [lossOf(left.value?.lossesW, key), lossOf(right.value?.lossesW, key)],
        itemStyle: { color: LOSS_COLOR[key] },
      })),
    },
    true,
  )
  requestAnimationFrame(() => {
    torqueChart?.resize()
    lossChart?.resize()
  })
}

function disposeCharts() {
  torqueChart?.dispose()
  lossChart?.dispose()
  torqueChart = null
  lossChart = null
}

async function loadScheme(kind: CompareScheme) {
  const seq = ++loadSeq
  loading.value = true
  errorMsg.value = ''
  disposeCharts()
  left.value = null
  right.value = null
  rawPair.value = null
  const urls = COMPARE_URLS[kind]
  try {
    const [lr, rr] = await Promise.all([fetch(urls.left), fetch(urls.right)])
    if (!lr.ok) throw new Error(`无法加载 ${urls.left}（${lr.status}）`)
    if (!rr.ok) throw new Error(`无法加载 ${urls.right}（${rr.status}）`)
    const rawL: unknown = await lr.json()
    const rawR: unknown = await rr.json()
    const parsedL = parseDriveCase(rawL)
    const parsedR = parseDriveCase(rawR)
    if (seq !== loadSeq) return
    rawPair.value = [rawL, rawR]
    left.value = parsedL
    right.value = parsedR
    await nextTick()
    if (seq !== loadSeq) return
    renderCharts()
  } catch (e) {
    if (seq !== loadSeq) return
    errorMsg.value = e instanceof Error ? e.message : String(e)
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

function download(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function exportJson() {
  if (!rawPair.value || !left.value || !right.value) return
  const body = {
    source: 'drive',
    scheme: scheme.value,
    cases: rawPair.value,
  }
  download(
    `${COMPARE_URLS[scheme.value].file}.json`,
    new Blob([`${JSON.stringify(body, null, 2)}\n`], { type: 'application/json' }),
  )
  ElMessage.success('已导出 JSON')
}

function exportCsv() {
  if (!left.value || !right.value) return
  download(
    `${COMPARE_URLS[scheme.value].file}.csv`,
    new Blob([`\uFEFF${compareCsv(left.value, right.value)}`], { type: 'text/csv;charset=utf-8' }),
  )
  ElMessage.success('已导出 CSV')
}

function onResize() {
  torqueChart?.resize()
  lossChart?.resize()
}

watch(scheme, (value) => {
  void loadScheme(value)
}, { immediate: true })

onMounted(() => window.addEventListener('resize', onResize))
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeCharts()
})
</script>

<style scoped>
.compare {
  min-height: 100%;
  padding: 16px 20px 28px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.compare-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px 16px;
}
.title { margin: 0; font-size: 15px; font-weight: 600; }
.desc { margin: 2px 0 0; color: var(--mo-text-muted); font-size: 12px; }
.toolbar-actions { margin-left: auto; display: flex; gap: 8px; }
.fixture-banner {
  padding: 8px 12px;
  border: 1px solid rgba(245, 158, 11, 0.45);
  background: var(--mo-amber-dim);
  color: var(--mo-amber);
  border-radius: var(--mo-radius);
  font-size: 12px;
  font-weight: 600;
}
.error-box {
  padding: 10px 12px;
  border-radius: var(--mo-radius);
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.35);
  color: #fca5a5;
  font-family: var(--mo-font-mono);
  font-size: 12px;
}
.compare-body { display: flex; flex-direction: column; gap: 12px; min-height: 160px; }
.scheme { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0; }
.pill {
  font-family: var(--mo-font-mono);
  font-size: 11px;
  color: var(--mo-accent);
  background: var(--mo-accent-dim);
  padding: 2px 6px;
  border-radius: var(--mo-radius-sm);
}
.card-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.summary-card {
  background: var(--mo-bg-elevated);
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius);
  padding: 12px 14px;
}
.summary-card[data-side='A'] { border-top: 2px solid var(--mo-accent); }
.summary-card[data-side='B'] { border-top: 2px solid var(--mo-amber); }
.card-head { display: flex; gap: 10px; }
.card-head h3 { margin: 0; font-size: 14px; }
.card-head p { margin: 2px 0 0; color: var(--mo-text-muted); font-size: 12px; font-family: var(--mo-font-mono); }
.side-tag {
  width: 22px; height: 22px; display: grid; place-items: center;
  border-radius: var(--mo-radius-sm); font-family: var(--mo-font-mono); font-size: 12px; font-weight: 600;
  color: var(--mo-text-inverse); background: var(--mo-accent);
}
.summary-card[data-side='B'] .side-tag { background: var(--mo-amber); }
.kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; margin: 12px 0 0; }
.kpi-grid dt { font-size: 11px; color: var(--mo-text-muted); }
.kpi-grid dd { margin: 0; font-family: var(--mo-font-mono); font-size: 18px; font-weight: 600; }
.kpi-grid dd span { margin-left: 4px; font-size: 11px; font-weight: 400; color: var(--mo-text-muted); }
.chart-grid { display: grid; grid-template-columns: 1.25fr 1fr; gap: 12px; }
.panel { background: var(--mo-bg-panel); border: 1px solid var(--mo-border); border-radius: var(--mo-radius); padding: 12px; }
.panel-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px; }
.panel-head h3 { margin: 0; font-size: 13px; }
.panel-unit { color: var(--mo-text-muted); font-size: 11px; font-family: var(--mo-font-mono); }
.chart { width: 100%; height: 280px; }
.metrics-table { width: 100%; }
.metrics-table :deep(.cell) { font-family: var(--mo-font-mono); font-size: 12px; }
.empty-hint { color: var(--mo-text-secondary); padding: 48px 0; text-align: center; }
@media (max-width: 960px) {
  .toolbar-actions { margin-left: 0; }
  .card-row, .chart-grid { grid-template-columns: 1fr; }
}
</style>
