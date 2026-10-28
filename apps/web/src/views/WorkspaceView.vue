<template>
  <div class="workspace">
    <aside class="workspace-side">
      <h2 class="side-title">工作区 · 几何预览</h2>
      <p class="side-desc">
        mesh {{ MESH_SCHEMA_VERSION }}
        <span v-if="projectId"> · projectId={{ projectId }}</span>
      </p>

      <div class="field">
        <label class="field-label">样例</label>
        <el-radio-group v-model="sampleKey" size="small" @change="onSampleChange">
          <el-radio-button
            v-for="opt in SAMPLE_OPTIONS"
            :key="opt.key"
            :value="opt.key"
          >
            {{ opt.label }}
          </el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="loadError" class="error-box">{{ loadError }}</div>

      <dl v-if="descriptor" class="meta-list">
        <div class="meta-row">
          <dt>kind</dt>
          <dd>{{ descriptor.kind }}</dd>
        </div>
        <div class="meta-row">
          <dt>machineType</dt>
          <dd>{{ descriptor.meta.machineType ?? '—' }}</dd>
        </div>
        <div class="meta-row">
          <dt>slotCount</dt>
          <dd>{{ descriptor.meta.slotCount ?? '—' }}</dd>
        </div>
        <div class="meta-row">
          <dt>poleCount</dt>
          <dd>{{ descriptor.meta.poleCount ?? '—' }}</dd>
        </div>
        <div v-if="polePairs != null" class="meta-row">
          <dt>极对数</dt>
          <dd>{{ polePairs }}</dd>
        </div>
        <div v-if="descriptor.meta.config" class="meta-row">
          <dt>config</dt>
          <dd>{{ descriptor.meta.config }}</dd>
        </div>
        <div v-if="descriptor.meta.diskCount != null" class="meta-row">
          <dt>diskCount</dt>
          <dd>{{ descriptor.meta.diskCount }}</dd>
        </div>
        <div v-if="descriptor.meta.airgap != null" class="meta-row">
          <dt>airgap</dt>
          <dd>{{ descriptor.meta.airgap }}</dd>
        </div>
        <div class="meta-row">
          <dt>primitives</dt>
          <dd>{{ descriptor.primitives.length }}</dd>
        </div>
        <div class="meta-row">
          <dt>units</dt>
          <dd>{{ descriptor.units.length }} / {{ descriptor.units.angle }}</dd>
        </div>
      </dl>

      <!-- P07: ACIM 导条占位编辑（本地 params，不重算 mesh） -->
      <section v-if="showAcimPanel && acimParams" class="acim-panel">
        <h3 class="panel-title">ACIM 导条（占位）</h3>
        <p class="panel-note">mesh 为样例快照，改字段仅更新本地 params 显示</p>

        <el-form label-position="top" size="small" class="acim-form">
          <el-form-item label="导条槽形 barSlotShape">
            <el-select v-model="acimParams.barSlotShape" style="width: 100%">
              <el-option label="rectangular" value="rectangular" />
              <el-option label="oval" value="oval" />
              <el-option label="closed_slot" value="closed_slot" />
              <el-option label="open_slot" value="open_slot" />
            </el-select>
          </el-form-item>

          <div class="pair-row">
            <el-form-item label="导条截面 width">
              <el-input-number
                v-model="acimParams.barCrossSection.width"
                :min="0.1"
                :step="0.5"
                controls-position="right"
              />
            </el-form-item>
            <el-form-item label="height">
              <el-input-number
                v-model="acimParams.barCrossSection.height"
                :min="0.1"
                :step="0.5"
                controls-position="right"
              />
            </el-form-item>
          </div>

          <div class="pair-row">
            <el-form-item label="端环截面 width">
              <el-input-number
                v-model="acimParams.endRingSection.width"
                :min="0.1"
                :step="0.5"
                controls-position="right"
              />
            </el-form-item>
            <el-form-item label="height">
              <el-input-number
                v-model="acimParams.endRingSection.height"
                :min="0.1"
                :step="0.5"
                controls-position="right"
              />
            </el-form-item>
          </div>

          <el-form-item label="barMaterialId">
            <el-input v-model="acimParams.barMaterialId" />
          </el-form-item>
          <el-form-item label="endRingMaterialId">
            <el-input v-model="acimParams.endRingMaterialId" />
          </el-form-item>
          <el-form-item label="cagePolePairs">
            <el-input-number
              v-model="acimParams.cagePolePairs"
              :min="1"
              :step="1"
              controls-position="right"
            />
          </el-form-item>
        </el-form>
      </section>

      <p class="hint">拖拽旋转 · 滚轮缩放 · AxesHelper</p>
    </aside>

    <section class="workspace-viewport">
      <Viewport3D :descriptor="descriptor" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Viewport3D from '@/components/Viewport3D.vue'
import { MESH_SCHEMA_VERSION, type MeshDescriptor } from '@/types/mesh'

type SampleKey = 'rf-pmsm' | 'rf-acim' | 'af-pmsm'

type AcimBlock = {
  barSlotShape: string
  barCrossSection: { width: number; height: number }
  endRingSection: { width: number; height: number }
  barMaterialId: string
  endRingMaterialId: string
  cagePolePairs: number
}

const SAMPLE_OPTIONS: {
  key: SampleKey
  label: string
  meshUrl: string
  paramsUrl: string
}[] = [
  {
    key: 'rf-pmsm',
    label: 'RF-PMSM',
    meshUrl: '/mesh/radial_pmsm_mesh.json',
    paramsUrl: '/mesh/radial_pmsm_params.json',
  },
  {
    key: 'rf-acim',
    label: 'RF-ACIM',
    meshUrl: '/mesh/radial_acim_mesh.json',
    paramsUrl: '/mesh/radial_acim_params.json',
  },
  {
    key: 'af-pmsm',
    label: 'AF-PMSM',
    meshUrl: '/mesh/axial_af_pmsm_rfmr_mesh.json',
    paramsUrl: '/mesh/axial_af_pmsm_rfmr_params.json',
  },
]

const route = useRoute()
const projectId = computed(() => {
  const q = route.query.projectId
  return typeof q === 'string' && q ? q : ''
})

const sampleKey = ref<SampleKey>('rf-pmsm')
const descriptor = ref<MeshDescriptor | null>(null)
const acimParams = ref<AcimBlock | null>(null)
const loadError = ref('')

const showAcimPanel = computed(
  () => sampleKey.value === 'rf-acim' || descriptor.value?.meta.machineType === 'ACIM',
)

const polePairs = computed(() => {
  const n = descriptor.value?.meta.poleCount
  if (typeof n !== 'number' || !Number.isFinite(n)) return null
  return n / 2
})

async function loadSample(key: SampleKey) {
  const opt = SAMPLE_OPTIONS.find((o) => o.key === key)
  if (!opt) return
  loadError.value = ''
  acimParams.value = null
  try {
    const meshRes = await fetch(opt.meshUrl)
    if (!meshRes.ok) throw new Error(`mesh ${meshRes.status} ${meshRes.statusText}`)
    const data = (await meshRes.json()) as MeshDescriptor
    if (data.schemaVersion !== MESH_SCHEMA_VERSION) {
      console.warn(
        `[Workspace] schemaVersion mismatch: got ${data.schemaVersion}, expected ${MESH_SCHEMA_VERSION}`,
      )
    }
    descriptor.value = data

    if (key === 'rf-acim') {
      const paramsRes = await fetch(opt.paramsUrl)
      if (!paramsRes.ok) throw new Error(`params ${paramsRes.status}`)
      const params = (await paramsRes.json()) as { acim?: AcimBlock }
      if (params.acim) {
        acimParams.value = {
          barSlotShape: params.acim.barSlotShape,
          barCrossSection: {
            width: params.acim.barCrossSection.width,
            height: params.acim.barCrossSection.height,
          },
          endRingSection: {
            width: params.acim.endRingSection.width,
            height: params.acim.endRingSection.height,
          },
          barMaterialId: params.acim.barMaterialId,
          endRingMaterialId: params.acim.endRingMaterialId,
          cagePolePairs: params.acim.cagePolePairs,
        }
      }
    }
  } catch (e) {
    descriptor.value = null
    acimParams.value = null
    loadError.value = e instanceof Error ? e.message : String(e)
  }
}

function onSampleChange() {
  void loadSample(sampleKey.value)
}

onMounted(() => {
  void loadSample(sampleKey.value)
})
</script>

<style scoped>
.workspace {
  display: flex;
  height: 100%;
  min-height: calc(100vh - var(--mo-header-h));
}

.workspace-side {
  width: 300px;
  flex-shrink: 0;
  padding: 16px;
  border-right: 1px solid var(--mo-border);
  background: var(--mo-bg-panel);
  overflow: auto;
}

.side-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.side-desc {
  margin: 4px 0 16px;
  color: var(--mo-text-muted);
  font-size: 11px;
  font-family: var(--mo-font-mono);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.field-label {
  font-size: 12px;
  color: var(--mo-text-secondary);
}

.meta-list {
  margin: 0 0 14px;
  padding: 10px 12px;
  background: var(--mo-bg-elevated);
  border: 1px solid var(--mo-border-subtle);
  border-radius: var(--mo-radius);
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

.acim-panel {
  margin-bottom: 12px;
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
  margin: 0 0 10px;
  font-size: 11px;
  color: var(--mo-text-muted);
}

.acim-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.acim-form :deep(.el-form-item__label) {
  margin-bottom: 2px;
  font-size: 11px;
  color: var(--mo-text-secondary);
  font-family: var(--mo-font-mono);
}

.pair-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.pair-row :deep(.el-input-number) {
  width: 100%;
}

.error-box {
  margin-bottom: 12px;
  padding: 8px 10px;
  border-radius: var(--mo-radius);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: var(--mo-danger);
  font-size: 12px;
}

.hint {
  margin: 16px 0 0;
  color: var(--mo-text-muted);
  font-size: 11px;
}

.workspace-viewport {
  flex: 1;
  min-width: 0;
  min-height: 0;
  position: relative;
}

:deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
}
</style>
