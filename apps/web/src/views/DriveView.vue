<template>
  <div class="drive">
    <aside class="drive-side">
      <h2 class="side-title">驱动 · Q4</h2>
      <p class="side-desc">
        solver-drive · Jobs jobType=drive
        <span v-if="projectLabel"> · {{ projectLabel }}</span>
      </p>

      <div class="field">
        <label class="field-label">机型</label>
        <el-radio-group v-model="machineType" size="small" @change="onMachineChange">
          <el-radio-button value="BLDC">BLDC</el-radio-button>
          <el-radio-button value="PMSM">PMSM</el-radio-button>
          <el-radio-button value="ACIM">ACIM</el-radio-button>
        </el-radio-group>
      </div>

      <div class="field">
        <label class="field-label">驱动模式</label>
        <el-select v-model="driveMode" size="small" style="width: 100%">
          <el-option
            v-for="o in modeOptions"
            :key="o.value"
            :label="o.label"
            :value="o.value"
          />
        </el-select>
      </div>

      <el-form label-position="top" size="small" class="param-form">
        <h3 class="section-title">operatingPoint</h3>
        <div class="form-grid">
          <el-form-item label="speedRpm">
            <el-input-number v-model="op.speedRpm" :min="0" :step="100" controls-position="right" />
          </el-form-item>
          <el-form-item label="torqueNm">
            <el-input-number v-model="op.torqueNm" :min="0" :step="0.5" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item label="tempC">
            <el-input-number v-model="op.tempC" :min="-40" :max="200" :step="5" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="driveMode === 'pmsm_foc' || driveMode === 'acim_foc'" label="iqA">
            <el-input-number v-model="op.iqA" :step="1" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="driveMode === 'pmsm_foc' || driveMode === 'acim_foc'" label="idA">
            <el-input-number v-model="op.idA" :step="0.5" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="driveMode === 'acim_vf'" label="slip">
            <el-input-number v-model="op.slip" :min="0.001" :max="0.5" :step="0.01" :precision="3" controls-position="right" />
          </el-form-item>
        </div>

        <h3 class="section-title">plant</h3>
        <div class="form-grid">
          <el-form-item label="Rs">
            <el-input-number v-model="plant.Rs" :min="0" :step="0.01" :precision="4" controls-position="right" />
          </el-form-item>
          <el-form-item label="p（极对数）">
            <el-input-number v-model="plant.p" :min="1" :step="1" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType !== 'ACIM'" label="psi_f">
            <el-input-number v-model="plant.psi_f" :min="0" :step="0.01" :precision="4" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'PMSM'" label="Ld">
            <el-input-number v-model="plant.Ld" :min="0" :step="0.0001" :precision="5" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'PMSM'" label="Lq">
            <el-input-number v-model="plant.Lq" :min="0" :step="0.0001" :precision="5" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="Lm">
            <el-input-number v-model="plant.Lm" :min="0" :step="0.01" :precision="4" controls-position="right" />
          </el-form-item>
          <el-form-item v-if="machineType === 'ACIM'" label="Rr">
            <el-input-number v-model="plant.Rr" :min="0" :step="0.01" :precision="4" controls-position="right" />
          </el-form-item>
          <el-form-item label="Vdc">
            <el-input-number v-model="plant.Vdc" :min="1" :step="1" controls-position="right" />
          </el-form-item>
        </div>

        <h3 class="section-title">PWM / 死区</h3>
        <div class="form-grid">
          <el-form-item label="carrierHz">
            <el-input-number v-model="pwm.carrierHz" :min="1000" :step="1000" controls-position="right" />
          </el-form-item>
          <el-form-item label="modIndex">
            <el-input-number v-model="pwm.modIndex" :min="0" :max="1.15" :step="0.05" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item label="scheme">
            <el-select v-model="pwm.scheme" style="width: 100%">
              <el-option value="svpwm" label="SVPWM" />
              <el-option value="spwm" label="SPWM" />
            </el-select>
          </el-form-item>
          <el-form-item label="tdeadUs">
            <el-input-number v-model="deadTime.tdeadUs" :min="0" :step="0.5" :precision="2" controls-position="right" />
          </el-form-item>
        </div>

        <h3 class="section-title">效率 Map 网格</h3>
        <div class="form-grid">
          <el-form-item label="nx（转速）">
            <el-input-number v-model="mapGrid.nx" :min="2" :max="40" :step="1" controls-position="right" />
          </el-form-item>
          <el-form-item label="ny（转矩）">
            <el-input-number v-model="mapGrid.ny" :min="2" :max="40" :step="1" controls-position="right" />
          </el-form-item>
          <el-form-item label="n min">
            <el-input-number v-model="mapGrid.speedRpmMin" :min="0" :step="100" controls-position="right" />
          </el-form-item>
          <el-form-item label="n max">
            <el-input-number v-model="mapGrid.speedRpmMax" :min="1" :step="100" controls-position="right" />
          </el-form-item>
          <el-form-item label="T min">
            <el-input-number v-model="mapGrid.torqueNmMin" :min="0" :step="0.5" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item label="T max">
            <el-input-number v-model="mapGrid.torqueNmMax" :min="0.1" :step="0.5" :precision="2" controls-position="right" />
          </el-form-item>
        </div>
      </el-form>

      <div class="side-actions">
        <el-button type="primary" :loading="running" @click="onRunCase">运行单工况</el-button>
        <el-button type="warning" :loading="mapping" @click="onRunMap">效率 Map</el-button>
      </div>
      <p class="side-hint">单工况与 Map 均走 Jobs（Celery / in-process）；不宣称误差指标。</p>
      <p v-if="jobStatus" class="side-backend">job={{ jobStatus }}</p>
    </aside>

    <section class="drive-main">
      <div v-if="errorMsg" class="error-box">{{ errorMsg }}</div>

      <div v-if="!caseResult && !mapResult && !errorMsg" class="empty-hint">
        选择机型与驱动模式后运行单工况，或提交效率 Map（默认 20×20，可改）。
      </div>

      <template v-if="caseResult">
        <div class="meta-banner">
          <span class="meta-pill">mode={{ caseResult.mode }}</span>
          <span class="meta-pill">solver={{ caseResult.meta?.solver || 'drive' }}</span>
          <span v-if="caseResult.meta?.elapsed_ms != null" class="meta-pill">
            {{ Number(caseResult.meta.elapsed_ms).toFixed(1) }} ms
          </span>
          <span v-if="caseResult.meta?.note" class="meta-note">{{ caseResult.meta.note }}</span>
        </div>

        <div class="kpi-row">
          <div class="kpi-card">
            <div class="kpi-label">平均转矩</div>
            <div class="kpi-value">
              {{ fmt(caseResult.metrics?.torqueAvgNm, 3) }}
              <span class="kpi-unit">N·m</span>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">脉动峰峰</div>
            <div class="kpi-value">
              {{ fmt(caseResult.metrics?.torqueRipplePpNm, 3) }}
              <span class="kpi-unit">N·m</span>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">效率</div>
            <div class="kpi-value">
              {{ fmtPct(caseResult.metrics?.efficiency) }}
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Irms</div>
            <div class="kpi-value">
              {{ fmt(caseResult.currentsA?.rmsPhase, 2) }}
              <span class="kpi-unit">A</span>
            </div>
          </div>
        </div>

        <div class="panels">
          <div class="panel">
            <h3 class="panel-title">损耗分离 lossesW</h3>
            <el-table :data="lossRows" size="small" stripe style="width: 100%">
              <el-table-column prop="name" label="项" min-width="120" />
              <el-table-column prop="value" label="W" min-width="100" />
            </el-table>
            <h3 class="panel-title" style="margin-top: 12px">currentsA</h3>
            <el-table :data="currentRows" size="small" stripe style="width: 100%">
              <el-table-column prop="name" label="项" min-width="120" />
              <el-table-column prop="value" label="A" min-width="100" />
            </el-table>
          </div>
          <div class="panel chart-panel">
            <h3 class="panel-title">电流 / 转矩波形</h3>
            <svg class="wave-svg" viewBox="0 0 640 220" preserveAspectRatio="none">
              <polyline
                v-for="(pl, idx) in wavePolylines"
                :key="idx"
                :points="pl.points"
                fill="none"
                :stroke="pl.color"
                stroke-width="1.5"
              />
            </svg>
            <div class="wave-legend">
              <span v-for="pl in wavePolylines" :key="pl.label" :style="{ color: pl.color }">{{ pl.label }}</span>
            </div>
          </div>
        </div>
      </template>

      <template v-if="mapResult">
        <div class="meta-banner" style="margin-top: 16px">
          <span class="meta-pill">efficiency_map</span>
          <span class="meta-pill">
            {{ mapResult.meta?.nx }}×{{ mapResult.meta?.ny }}
          </span>
          <span class="meta-pill">
            valid={{ mapResult.meta?.validCells }}/{{ mapResult.meta?.totalCells }}
          </span>
        </div>
        <div class="panel">
          <h3 class="panel-title">效率 Map（色块）</h3>
          <div
            class="eff-grid"
            :style="{
              gridTemplateColumns: `repeat(${mapResult.axes?.speedRpm?.length || 1}, minmax(12px, 1fr))`,
            }"
          >
            <template v-for="(row, j) in mapResult.efficiency" :key="'r' + j">
              <div
                v-for="(cell, i) in row"
                :key="j + '-' + i"
                class="eff-cell"
                :title="cellTitle(i, j, cell)"
                :style="{ background: effColor(cell) }"
              />
            </template>
          </div>
          <p class="map-axes">
            横轴 speedRpm {{ mapResult.axes?.speedRpm?.[0] }}…{{
              mapResult.axes?.speedRpm?.[(mapResult.axes?.speedRpm?.length || 1) - 1]
            }}
            · 纵轴 torqueNm {{ mapResult.axes?.torqueNm?.[0] }}…{{
              mapResult.axes?.torqueNm?.[(mapResult.axes?.torqueNm?.length || 1) - 1]
            }}
            （行=转矩↑）
          </p>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { createJob, pollJob } from '@/api/jobs'
import type { DriveJobPayload, DriveMode, MachineType } from '@/api/types'
import { composeDrivePayloadFromUem } from '@/lib/composeDrivePayload'
import { useProjectSession } from '@/stores/projectSession'
import { useProjectsStore } from '@/stores/projects'

const route = useRoute()
const projects = useProjectsStore()
const session = useProjectSession()

const machineType = ref<MachineType>(session.projectMeta.machineType || 'PMSM')
const driveMode = ref<DriveMode>(
  (session.excitation.driveDraft?.mode as DriveMode) || 'pmsm_foc',
)
const running = ref(false)
const mapping = ref(false)
const errorMsg = ref('')
const jobStatus = ref('')
const caseResult = ref<Record<string, any> | null>(null)
const mapResult = ref<Record<string, any> | null>(null)

const op = reactive({
  speedRpm: 3000,
  torqueNm: 5,
  tempC: 80,
  iqA: 10,
  idA: 0,
  slip: 0.03,
})

const plant = reactive({
  Rs: 0.05,
  p: 4,
  psi_f: 0.08,
  Ld: 0.001,
  Lq: 0.0012,
  Lm: 0.08,
  Rr: 0.04,
  Vdc: 48,
})

const pwm = reactive({
  carrierHz: 10000,
  modIndex: 0.9,
  scheme: 'svpwm' as 'svpwm' | 'spwm',
})

const deadTime = reactive({
  tdeadUs: session.excitation.driveDraft?.deadTime?.tdeadUs ?? 1.0,
})

const _seedPwm = session.excitation.driveDraft?.pwm
if (_seedPwm?.carrierHz != null) pwm.carrierHz = _seedPwm.carrierHz
if (_seedPwm?.modIndex != null) pwm.modIndex = _seedPwm.modIndex
if (_seedPwm?.scheme === 'svpwm' || _seedPwm?.scheme === 'spwm') pwm.scheme = _seedPwm.scheme

const _seedOp = session.excitation.operatingPoint
if (typeof _seedOp.speed_rpm === 'number') op.speedRpm = _seedOp.speed_rpm
if (typeof session.excitation.driveDraft?.iqA === 'number') op.iqA = session.excitation.driveDraft.iqA
else if (typeof _seedOp.current_a_peak === 'number') op.iqA = _seedOp.current_a_peak
if (typeof session.excitation.driveDraft?.idA === 'number') op.idA = session.excitation.driveDraft.idA
if (typeof session.excitation.driveDraft?.torqueNm === 'number') op.torqueNm = session.excitation.driveDraft.torqueNm
if (typeof session.excitation.driveDraft?.tempC === 'number') op.tempC = session.excitation.driveDraft.tempC
if (typeof session.excitation.driveDraft?.slip === 'number') op.slip = session.excitation.driveDraft.slip
else if (typeof _seedOp.slip === 'number') op.slip = _seedOp.slip

function syncDraftToSession() {
  session.setDriveDraft({
    mode: driveMode.value,
    pwm: { carrierHz: pwm.carrierHz, modIndex: pwm.modIndex, scheme: pwm.scheme },
    deadTime: { tdeadUs: deadTime.tdeadUs },
    iqA: op.iqA,
    idA: op.idA,
    torqueNm: op.torqueNm,
    tempC: op.tempC,
    slip: op.slip,
  })
  session.commitOperatingPoint({ speed_rpm: op.speedRpm })
}

watch([driveMode, () => pwm.carrierHz, () => pwm.modIndex, () => pwm.scheme, () => deadTime.tdeadUs], () => {
  syncDraftToSession()
})

const mapGrid = reactive({
  nx: 20,
  ny: 20,
  speedRpmMin: 500,
  speedRpmMax: 6000,
  torqueNmMin: 0.5,
  torqueNmMax: 10,
})

const modeOptions = computed(() => {
  if (machineType.value === 'BLDC') {
    return [{ value: 'bldc_square' as DriveMode, label: 'BLDC 方波 / 六步' }]
  }
  if (machineType.value === 'PMSM') {
    return [{ value: 'pmsm_foc' as DriveMode, label: 'PMSM FOC' }]
  }
  return [
    { value: 'acim_vf' as DriveMode, label: 'ACIM V/f' },
    { value: 'acim_foc' as DriveMode, label: 'ACIM 感应 FOC' },
  ]
})

const projectLabel = computed(() => {
  const id = route.query.projectId as string | undefined
  const p = id ? projects.items.find((x) => x.id === id) : projects.items[0]
  return p ? `${p.name} (${p.machineType})` : ''
})

function onMachineChange() {
  const opts = modeOptions.value
  if (!opts.find((o) => o.value === driveMode.value)) {
    driveMode.value = opts[0].value
  }
  if (machineType.value === 'ACIM') {
    plant.Vdc = 540
    plant.p = 2
    op.speedRpm = 1450
  } else {
    plant.Vdc = 48
    plant.p = 4
    op.speedRpm = 3000
  }
}

function fmt(v: unknown, dig = 2): string {
  if (v == null || typeof v !== 'number' || Number.isNaN(v)) return '—'
  return v.toFixed(dig)
}

function fmtPct(v: unknown): string {
  if (v == null || typeof v !== 'number' || Number.isNaN(v)) return '—'
  return `${(v * 100).toFixed(1)}%`
}

const lossRows = computed(() => {
  const L = caseResult.value?.lossesW || {}
  return [
    { name: 'copper', value: fmt(L.copper, 3) },
    { name: 'iron', value: fmt(L.iron, 3) },
    { name: 'magnetEddy', value: fmt(L.magnetEddy, 3) },
    { name: 'bar', value: fmt(L.bar, 3) },
    { name: 'endRing', value: fmt(L.endRing, 3) },
  ]
})

const currentRows = computed(() => {
  const C = caseResult.value?.currentsA || {}
  return [
    { name: 'rmsPhase', value: fmt(C.rmsPhase, 3) },
    { name: 'id', value: fmt(C.id, 3) },
    { name: 'iq', value: fmt(C.iq, 3) },
  ]
})

const wavePolylines = computed(() => {
  const wf = caseResult.value?.waveforms
  if (!wf?.t_s?.length) return []
  const series = [
    { key: 'ia', color: '#38bdf8', label: 'ia' },
    { key: 'ib', color: '#a78bfa', label: 'ib' },
    { key: 'ic', color: '#34d399', label: 'ic' },
    { key: 'torque_nm', color: '#fbbf24', label: 'T' },
  ]
  const w = 640
  const h = 200
  const pad = 10
  return series
    .map((s) => {
      const arr: number[] = wf[s.key] || []
      if (!arr.length) return null
      const ymin = Math.min(...arr)
      const ymax = Math.max(...arr)
      const span = ymax - ymin || 1
      const pts = arr
        .map((y, i) => {
          const x = pad + (i / Math.max(arr.length - 1, 1)) * (w - 2 * pad)
          const yy = pad + (1 - (y - ymin) / span) * (h - 2 * pad)
          return `${x.toFixed(1)},${yy.toFixed(1)}`
        })
        .join(' ')
      return { ...s, points: pts }
    })
    .filter(Boolean) as { label: string; color: string; points: string }[]
})

function effColor(cell: number | null): string {
  if (cell == null || Number.isNaN(cell)) return 'rgba(100,116,139,0.25)'
  const t = Math.max(0, Math.min(1, (cell - 0.5) / 0.5))
  const r = Math.round(30 + t * 20)
  const g = Math.round(80 + t * 140)
  const b = Math.round(120 - t * 40)
  return `rgb(${r},${g},${b})`
}

function cellTitle(i: number, j: number, cell: number | null): string {
  const n = mapResult.value?.axes?.speedRpm?.[i]
  const t = mapResult.value?.axes?.torqueNm?.[j]
  return `n=${n} T=${t} η=${cell == null ? 'n/a' : (cell * 100).toFixed(1) + '%'}`
}

function buildPayload(mode: DriveMode | 'efficiency_map'): DriveJobPayload {
  syncDraftToSession()
  const composed = composeDrivePayloadFromUem({
    machineType: machineType.value,
    excitation: {
      operatingPoint: {
        speed_rpm: op.speedRpm,
        current_a_peak: op.iqA,
        slip: op.slip,
      },
      driveDraft: {
        mode: driveMode.value,
        pwm: { ...pwm },
        deadTime: { ...deadTime },
        iqA: op.iqA,
        idA: op.idA,
        torqueNm: op.torqueNm,
        tempC: op.tempC,
        slip: op.slip,
      },
    },
    map:
      mode === 'efficiency_map'
        ? { mapGrid: { ...mapGrid }, mapMode: driveMode.value }
        : undefined,
  })
  // plant 仍由本页本地参数补齐（UEM 草稿不承载 plant）
  composed.plant = { ...plant }
  return composed
}

async function ensureProjectId(): Promise<string> {
  const q = route.query.projectId as string | undefined
  if (q) return q
  if (!projects.items.length) {
    try {
      await projects.fetchProjects()
    } catch {
      /* ignore — may create below */
    }
  }
  if (projects.items[0]?.id) return projects.items[0].id
  const created = await projects.addProject({
    name: 'Drive Q4 demo',
    topology: 'RF',
    machineType: machineType.value,
  })
  return created.id
}

async function onRunCase() {
  running.value = true
  errorMsg.value = ''
  caseResult.value = null
  jobStatus.value = 'queued'
  try {
    const projectId = await ensureProjectId()
    const payload = buildPayload(driveMode.value)
    const created = await createJob({ projectId, jobType: 'drive', payload })
    jobStatus.value = created.status
    const final = await pollJob(created.id, {
      intervalMs: 400,
      timeoutMs: 60_000,
      onUpdate: (j) => {
        jobStatus.value = j.status
      },
    })
    if (final.status !== 'succeeded') {
      throw new Error(final.error?.message || `job ${final.status}`)
    }
    const result = (final.payload as any)?.result
    if (!result) throw new Error('Job succeeded but payload.result missing')
    caseResult.value = result
  } catch (e: any) {
    errorMsg.value = e?.message || String(e)
  } finally {
    running.value = false
  }
}

async function onRunMap() {
  mapping.value = true
  errorMsg.value = ''
  mapResult.value = null
  jobStatus.value = 'queued'
  try {
    const projectId = await ensureProjectId()
    const payload = buildPayload('efficiency_map')
    const created = await createJob({ projectId, jobType: 'drive', payload })
    const final = await pollJob(created.id, {
      intervalMs: 500,
      timeoutMs: 180_000,
      onUpdate: (j) => {
        jobStatus.value = j.status
      },
    })
    if (final.status !== 'succeeded') {
      throw new Error(final.error?.message || `job ${final.status}`)
    }
    const result = (final.payload as any)?.result
    if (!result) throw new Error('Map job succeeded but payload.result missing')
    mapResult.value = result
  } catch (e: any) {
    errorMsg.value = e?.message || String(e)
  } finally {
    mapping.value = false
  }
}
</script>

<style scoped>
.drive {
  display: flex;
  height: 100%;
  min-height: 0;
}
.drive-side {
  width: 340px;
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
  flex-wrap: wrap;
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
.drive-main {
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
.wave-svg {
  width: 100%;
  height: 220px;
  background: var(--mo-bg-elevated);
  border-radius: var(--mo-radius-sm);
}
.wave-legend {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 11px;
  font-family: var(--mo-font-mono);
}
.eff-grid {
  display: grid;
  gap: 2px;
  min-height: 200px;
}
.eff-cell {
  aspect-ratio: 1;
  border-radius: 2px;
  min-height: 10px;
}
.map-axes {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--mo-text-muted);
  font-family: var(--mo-font-mono);
}
@media (max-width: 960px) {
  .drive {
    flex-direction: column;
  }
  .drive-side {
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
