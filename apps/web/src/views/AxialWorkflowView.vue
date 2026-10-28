<template>
  <div class="axial">
    <aside class="axial-side">
      <h2 class="side-title">轴向 · AF-PMSM</h2>
      <p class="side-desc">
        Q3-2 全流程 · geometry → 解析 → FEM 入口
        <span v-if="projectLabel"> · {{ projectLabel }}</span>
      </p>

      <div v-if="loadError" class="error-box">{{ loadError }}</div>

      <div class="field">
        <label class="field-label">构型 config</label>
        <el-radio-group v-model="config" size="small" @change="onConfigChange">
          <el-radio-button value="RFMR">RFMR</el-radio-button>
          <el-radio-button value="FRMF">FRMF</el-radio-button>
        </el-radio-group>
      </div>

      <el-form label-position="top" size="small" class="param-form">
        <h3 class="section-title">pmsm 几何（mm）</h3>
        <div class="form-grid">
          <el-form-item label="innerDiameter">
            <el-input-number v-model="pmsm.innerDiameter" :min="1" :step="1" :precision="1" controls-position="right" @change="onParamsEdit" />
          </el-form-item>
          <el-form-item label="outerDiameter">
            <el-input-number v-model="pmsm.outerDiameter" :min="2" :step="1" :precision="1" controls-position="right" @change="onParamsEdit" />
          </el-form-item>
          <el-form-item label="diskCount">
            <el-input-number v-model="pmsm.diskCount" :min="1" :step="1" controls-position="right" @change="onParamsEdit" />
          </el-form-item>
          <el-form-item label="diskThickness">
            <el-input-number v-model="pmsm.diskThickness" :min="0.1" :step="0.5" :precision="2" controls-position="right" @change="onParamsEdit" />
          </el-form-item>
          <el-form-item label="airgap">
            <el-input-number v-model="pmsm.airgap" :min="0.1" :step="0.1" :precision="2" controls-position="right" @change="onParamsEdit" />
          </el-form-item>
          <el-form-item label="magnetSectorAngle">
            <el-input-number v-model="pmsm.magnetSectorAngle" :min="1" :max="180" :step="5" controls-position="right" @change="onParamsEdit" />
          </el-form-item>
          <el-form-item label="slotCount">
            <el-input-number v-model="pmsm.slotCount" :min="3" :step="1" controls-position="right" @change="onParamsEdit" />
          </el-form-item>
          <el-form-item label="poleCount">
            <el-input-number v-model="pmsm.poleCount" :min="2" :step="2" controls-position="right" @change="onParamsEdit" />
          </el-form-item>
        </div>

        <h3 class="section-title">工况（解析）</h3>
        <div class="form-grid">
          <el-form-item label="speed_rpm">
            <el-input-number v-model="op.speed_rpm" :min="0" :step="100" controls-position="right" />
          </el-form-item>
          <el-form-item label="current_a_peak">
            <el-input-number v-model="op.current_a_peak" :min="0" :step="1" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item label="gamma_deg">
            <el-input-number v-model="op.gamma_deg" :min="-90" :max="90" :step="5" controls-position="right" />
          </el-form-item>
          <el-form-item label="br_t">
            <el-input-number v-model="materials.br_t" :min="0.1" :max="1.6" :step="0.05" :precision="2" controls-position="right" />
          </el-form-item>
        </div>
      </el-form>

      <dl class="meta-list">
        <div class="meta-row">
          <dt>topology</dt>
          <dd>AF</dd>
        </div>
        <div class="meta-row">
          <dt>machineType</dt>
          <dd>PMSM</dd>
        </div>
        <div class="meta-row">
          <dt>极对数（展示）</dt>
          <dd>{{ polePairs }}</dd>
        </div>
        <div class="meta-row">
          <dt>stack_length_m</dt>
          <dd>{{ geometrySummary.stack_length_m.toFixed(4) }}</dd>
        </div>
        <div class="meta-row">
          <dt>rotor_od_m</dt>
          <dd>{{ geometrySummary.rotor_od_m.toFixed(4) }}</dd>
        </div>
        <div class="meta-row">
          <dt>stator_id_m</dt>
          <dd>{{ geometrySummary.stator_id_m.toFixed(4) }}</dd>
        </div>
        <div class="meta-row">
          <dt>mesh</dt>
          <dd>{{ descriptor ? `${descriptor.kind} · ${descriptor.primitives.length} prims` : '—' }}</dd>
        </div>
      </dl>

      <div class="side-actions">
        <el-button type="primary" :loading="solving" @click="onSolve">解析求解</el-button>
        <el-button :disabled="solving" @click="reloadEntry">恢复样例</el-button>
      </div>
      <p class="side-hint">
        AF 降级：sync → fixture（Wasm AF 未落地）。待 sync/Jobs 金标常驻。
      </p>
      <p v-if="solveBackendLabel" class="side-backend">路径：{{ solveBackendLabel }}</p>

      <section class="fem-hint">
        <h3 class="panel-title">FEM 入口</h3>
        <p class="panel-note">femEntryHint {{ femHint.schemaVersion }} · 无网格</p>
        <dl class="meta-list compact">
          <div class="meta-row"><dt>diskCount</dt><dd>{{ femHint.diskCount }}</dd></div>
          <div class="meta-row"><dt>poleCount</dt><dd>{{ femHint.poleCount }}</dd></div>
          <div class="meta-row"><dt>config</dt><dd>{{ femHint.config ?? '—' }}</dd></div>
        </dl>
        <el-button size="small" type="warning" plain @click="goField">打开场量可视化</el-button>
      </section>
    </aside>

    <section class="axial-main">
      <div class="viewport-wrap">
        <Viewport3D :descriptor="descriptor" />
      </div>

      <div v-if="errorMsg" class="error-box">{{ errorMsg }}</div>

      <template v-if="result">
        <div class="meta-banner" :data-mock="result.meta.mock">
          <span class="meta-pill">path={{ result.meta.source || solveBackend || '—' }}</span>
          <span class="meta-pill">solver={{ result.meta.solver }}</span>
          <span class="meta-pill">mock={{ result.meta.mock }}</span>
          <span class="meta-pill">{{ Number(result.meta.elapsed_ms).toFixed(2) }} ms</span>
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
      </template>
      <div v-else-if="!errorMsg" class="empty-hint">
        静态 mesh 来自 pipeline_entry；调参后本地重算 summary/hint。点「解析求解」走 sync→fixture。
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Viewport3D from '@/components/Viewport3D.vue'
import {
  buildFemEntryHintLocal,
  summarizeAxialPmsmLocal,
  type AxialGeometryParams,
  type AxialPipelineEntry,
  type AxialPmsmParams,
  type FemEntryHint,
} from '@/types/axial'
import type { GeometrySummary, Materials, OperatingPoint, SolveBackend, SolveResult } from '@/types/solver'
import type { MeshDescriptor } from '@/types/mesh'
import { getAxialSolveBackend, loadAxialSampleRequest, solveAxial } from '@/lib/axialSolve'
import { useProjectsStore } from '@/stores/projects'

const PIPELINE_URL = '/geometry/axial_af_pmsm_rfmr_pipeline_entry.json'

const route = useRoute()
const router = useRouter()
const projects = useProjectsStore()

const loadError = ref<string | null>(null)
const entry = ref<AxialPipelineEntry | null>(null)
const descriptor = ref<MeshDescriptor | null>(null)
const config = ref<'RFMR' | 'FRMF'>('RFMR')
const pmsm = reactive<AxialPmsmParams>({
  innerDiameter: 40,
  outerDiameter: 120,
  diskCount: 3,
  airgap: 1,
  diskThickness: 8,
  magnetSectorAngle: 150,
  slotCount: 12,
  poleCount: 10,
})
const op = reactive<OperatingPoint>({
  speed_rpm: 3000,
  current_a_peak: 20,
  gamma_deg: 0,
})
const materials = reactive<Materials>({
  steel_id: 'demo-steel',
  magnet_id: 'demo-N35',
  conductor_id: 'Cu',
  br_t: 1.2,
})

const solving = ref(false)
const result = ref<SolveResult | null>(null)
const errorMsg = ref<string | null>(null)
const solveBackend = ref<SolveBackend | null>(null)

const polePairs = computed(() => pmsm.poleCount / 2)

const geometryParamsLocal = computed<AxialGeometryParams>(() => ({
  schemaVersion: entry.value?.geometryParams.schemaVersion ?? '0.1.0-q1',
  topology: 'AF',
  machineType: 'PMSM',
  config: config.value,
  units: entry.value?.geometryParams.units ?? { length: 'mm', angle: 'deg' },
  pmsm: { ...pmsm },
}))

const geometrySummary = computed<GeometrySummary>(() => {
  // 调参后本地重算 summary（对齐 Mo-几何 tip：poles=poleCount，stack=diskThickness/1000）
  return summarizeAxialPmsmLocal(geometryParamsLocal.value)
})

const femHint = computed<FemEntryHint>(() => {
  return buildFemEntryHintLocal(geometryParamsLocal.value)
})

const solveBackendLabel = computed(() => {
  const b = result.value?.meta.source ?? solveBackend.value
  const labels: Record<string, string> = {
    sync: 'sync HTTP (axial_planes 金标)',
    fixture: 'fixture',
    mock: 'mock',
  }
  return b ? labels[b] ?? b : ''
})

const projectLabel = computed(() => {
  const id = typeof route.query.projectId === 'string' ? route.query.projectId : ''
  if (!id) return ''
  const p = projects.items.find((x) => x.id === id)
  return p ? `${p.name} (${id})` : `projectId=${id}`
})

function fmt(n: number, digits: number): string {
  if (!Number.isFinite(n)) return '—'
  return n.toFixed(digits)
}

function applyEntry(e: AxialPipelineEntry) {
  entry.value = e
  descriptor.value = e.meshDescriptor
  config.value = (e.geometryParams.config as 'RFMR' | 'FRMF') || 'RFMR'
  Object.assign(pmsm, e.geometryParams.pmsm)
  const stub = e.analyticSolveStub
  if (stub.operating_point) {
    op.speed_rpm = stub.operating_point.speed_rpm || 3000
    op.current_a_peak = stub.operating_point.current_a_peak ?? 20
    op.gamma_deg = stub.operating_point.gamma_deg ?? 0
  }
  if (stub.materials && Object.keys(stub.materials).length) {
    Object.assign(materials, stub.materials)
  }
}

async function reloadEntry() {
  loadError.value = null
  result.value = null
  errorMsg.value = null
  solveBackend.value = null
  try {
    const res = await fetch(PIPELINE_URL)
    if (!res.ok) throw new Error(`pipeline_entry ${res.status}`)
    const data = (await res.json()) as AxialPipelineEntry
    applyEntry(data)
    // 用金标样例请求补齐工况（pipeline stub 的 speed=0）
    try {
      const sample = await loadAxialSampleRequest()
      op.speed_rpm = sample.operating_point.speed_rpm
      op.current_a_peak = sample.operating_point.current_a_peak ?? 20
      op.gamma_deg = sample.operating_point.gamma_deg ?? 0
      if (sample.materials) Object.assign(materials, sample.materials)
    } catch {
      /* keep stub ops */
    }
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : String(e)
    entry.value = null
    descriptor.value = null
  }
}

function onParamsEdit() {
  // mesh 本 tip 保持静态 snapshot；summary/hint 由 computed 重算
  result.value = null
}

function onConfigChange() {
  onParamsEdit()
}

function buildSolveRequest() {
  const summary = geometrySummary.value
  return {
    schema_version: '0.0.0-gate0' as const,
    topology: 'AF' as const,
    machine_type: 'PMSM' as const,
    geometry: {
      ...summary,
      n_planes: 4,
      magnet_thickness_m: summary.magnet_thickness_m ?? 0.004,
      turns_per_phase: 36,
    },
    materials: { ...materials },
    operating_point: { ...op },
  }
}

async function onSolve() {
  solving.value = true
  errorMsg.value = null
  try {
    const req = buildSolveRequest()
    const r = await solveAxial(req)
    result.value = r
    solveBackend.value = getAxialSolveBackend()
  } catch (e) {
    result.value = null
    errorMsg.value = e instanceof Error ? e.message : String(e)
  } finally {
    solving.value = false
  }
}

function goField() {
  router.push({
    name: 'field',
    query: {
      from: 'axial',
      poles: String(pmsm.poleCount),
      disks: String(pmsm.diskCount),
    },
  })
}

onMounted(() => {
  void reloadEntry()
})
</script>

<style scoped>
.axial {
  display: flex;
  height: 100%;
  min-height: calc(100vh - var(--mo-header-h));
}

.axial-side {
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

.meta-list {
  margin: 12px 0;
  padding: 10px 12px;
  background: var(--mo-bg-elevated);
  border: 1px solid var(--mo-border-subtle);
  border-radius: var(--mo-radius);
}

.meta-list.compact {
  margin-top: 8px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 3px 0;
  font-size: 12px;
}

.meta-row dt {
  color: var(--mo-text-muted);
  font-family: var(--mo-font-mono);
}

.meta-row dd {
  margin: 0;
  color: var(--mo-text-primary);
  font-family: var(--mo-font-mono);
}

.side-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
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

.fem-hint {
  margin-top: 16px;
  padding: 10px 12px;
  background: var(--mo-bg-elevated);
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: var(--mo-radius);
}

.panel-title {
  margin: 0 0 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--mo-amber);
}

.panel-note {
  margin: 0 0 8px;
  font-size: 11px;
  color: var(--mo-text-muted);
}

.axial-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  overflow: auto;
  gap: 12px;
}

.viewport-wrap {
  flex: 1;
  min-height: 320px;
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius);
  overflow: hidden;
  background: var(--mo-bg-base);
}

.empty-hint {
  color: var(--mo-text-secondary);
  padding: 12px 0;
  text-align: center;
  font-size: 13px;
}

.error-box {
  margin-bottom: 8px;
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

@media (max-width: 960px) {
  .axial {
    flex-direction: column;
  }
  .axial-side {
    width: 100%;
    max-height: 42vh;
    border-right: none;
    border-bottom: 1px solid var(--mo-border);
  }
  .kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
