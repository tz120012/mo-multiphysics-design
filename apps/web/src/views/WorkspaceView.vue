<template>
  <div class="workspace">
    <aside class="workspace-side">
      <h2 class="side-title">工作区 · 几何预览</h2>
      <p class="side-desc">
        mesh {{ MESH_SCHEMA_VERSION }}
        <span v-if="projectId"> · projectId={{ projectId }}</span>
      </p>

      <!-- Q1-6 / P04 Undo/Redo -->
      <div class="history-bar">
        <el-button
          size="small"
          :disabled="!history.canUndo"
          title="撤销 (Ctrl/Cmd+Z)"
          @click="onUndo"
        >
          撤销
        </el-button>
        <el-button
          size="small"
          :disabled="!history.canRedo"
          title="重做 (Ctrl/Cmd+Shift+Z / Ctrl+Y)"
          @click="onRedo"
        >
          重做
        </el-button>
        <span class="history-meta" title="cursor / entries">
          {{ history.cursor }}/{{ history.entries.length }}
        </span>
      </div>

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

      <!-- P07: ACIM 导条占位编辑（本地 params，不重算 mesh）；变更走命令栈 -->
      <section v-if="showAcimPanel && acimParams" class="acim-panel">
        <h3 class="panel-title">ACIM 导条（占位）</h3>
        <p class="panel-note">mesh 为样例快照，改字段仅更新本地 params 显示</p>

        <el-form label-position="top" size="small" class="acim-form">
          <el-form-item label="导条槽形 barSlotShape">
            <el-select
              :model-value="acimParams.barSlotShape"
              style="width: 100%"
              @change="onBarSlotShape"
            >
              <el-option label="rectangular" value="rectangular" />
              <el-option label="oval" value="oval" />
              <el-option label="closed_slot" value="closed_slot" />
              <el-option label="open_slot" value="open_slot" />
            </el-select>
          </el-form-item>

          <div class="pair-row">
            <el-form-item label="导条截面 width">
              <el-input-number
                :model-value="acimParams.barCrossSection.width"
                :min="0.1"
                :step="0.5"
                controls-position="right"
                @change="onBarWidth"
              />
            </el-form-item>
            <el-form-item label="height">
              <el-input-number
                :model-value="acimParams.barCrossSection.height"
                :min="0.1"
                :step="0.5"
                controls-position="right"
                @change="onBarHeight"
              />
            </el-form-item>
          </div>

          <div class="pair-row">
            <el-form-item label="端环截面 width">
              <el-input-number
                :model-value="acimParams.endRingSection.width"
                :min="0.1"
                :step="0.5"
                controls-position="right"
                @change="onEndRingWidth"
              />
            </el-form-item>
            <el-form-item label="height">
              <el-input-number
                :model-value="acimParams.endRingSection.height"
                :min="0.1"
                :step="0.5"
                controls-position="right"
                @change="onEndRingHeight"
              />
            </el-form-item>
          </div>

          <el-form-item label="barMaterialId">
            <el-input
              :model-value="acimParams.barMaterialId"
              @change="onBarMaterialId"
            />
          </el-form-item>
          <el-form-item label="endRingMaterialId">
            <el-input
              :model-value="acimParams.endRingMaterialId"
              @change="onEndRingMaterialId"
            />
          </el-form-item>
          <el-form-item label="cagePolePairs">
            <el-input-number
              :model-value="acimParams.cagePolePairs"
              :min="1"
              :step="1"
              controls-position="right"
              @change="onCagePolePairs"
            />
          </el-form-item>
        </el-form>
      </section>

      <p class="hint">拖拽旋转 · 滚轮缩放 · AxesHelper · Ctrl/Cmd+Z 撤销</p>
    </aside>

    <section class="workspace-viewport">
      <Viewport3D :descriptor="descriptor" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Viewport3D from '@/components/Viewport3D.vue'
import { useHistoryStore } from '@/stores/history'
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
const history = useHistoryStore()

const projectId = computed(() => {
  const q = route.query.projectId
  return typeof q === 'string' && q ? q : ''
})

const sampleKey = ref<SampleKey>('rf-pmsm')
const descriptor = ref<MeshDescriptor | null>(null)
const acimParams = ref<AcimBlock | null>(null)
const loadError = ref('')

/** undo/redo 回写时跳过 push，避免回环 */
let applyingHistory = false

const showAcimPanel = computed(
  () => sampleKey.value === 'rf-acim' || descriptor.value?.meta.machineType === 'ACIM',
)

const polePairs = computed(() => {
  const n = descriptor.value?.meta.poleCount
  if (typeof n !== 'number' || !Number.isFinite(n)) return null
  return n / 2
})

function getAcimPath(path: string): unknown {
  const root = acimParams.value
  if (!root) return undefined
  const parts = path.split('.')
  let cur: unknown = root
  for (const p of parts) {
    if (cur == null || typeof cur !== 'object') return undefined
    cur = (cur as Record<string, unknown>)[p]
  }
  return cur
}

function setAcimPath(path: string, value: unknown) {
  const root = acimParams.value
  if (!root) return
  const parts = path.split('.')
  if (parts.length === 1) {
    ;(root as unknown as Record<string, unknown>)[parts[0]] = value
    return
  }
  let cur: Record<string, unknown> = root as unknown as Record<string, unknown>
  for (let i = 0; i < parts.length - 1; i++) {
    const next = cur[parts[i]]
    if (next == null || typeof next !== 'object') return
    cur = next as Record<string, unknown>
  }
  cur[parts[parts.length - 1]] = value
}

/**
 * 几何/ACIM 字段变更 → push geometry.params.set（契约 Q1-6）
 * path 相对 acimParams（如 barCrossSection.width）；payload.path 带 acim. 前缀
 */
function commitAcim(path: string, next: unknown) {
  if (applyingHistory || acimParams.value == null) return
  if (next === undefined || next === null) return
  const before = getAcimPath(path)
  if (Object.is(before, next)) return
  setAcimPath(path, next)
  const fullPath = `acim.${path}`
  history.push({
    commandType: 'geometry.params.set',
    summary: `设置 ${fullPath} = ${String(next)}`,
    payload: { path: fullPath, before, after: next },
    inverse: { path: fullPath, before: next, after: before },
  })
}

function onBarSlotShape(v: string) {
  commitAcim('barSlotShape', v)
}
function onBarWidth(v: number | undefined) {
  commitAcim('barCrossSection.width', v)
}
function onBarHeight(v: number | undefined) {
  commitAcim('barCrossSection.height', v)
}
function onEndRingWidth(v: number | undefined) {
  commitAcim('endRingSection.width', v)
}
function onEndRingHeight(v: number | undefined) {
  commitAcim('endRingSection.height', v)
}
function onBarMaterialId(v: string) {
  commitAcim('barMaterialId', v)
}
function onEndRingMaterialId(v: string) {
  commitAcim('endRingMaterialId', v)
}
function onCagePolePairs(v: number | undefined) {
  commitAcim('cagePolePairs', v)
}

function applyGeometryEntry(
  entry: {
    commandType: string
    payload?: Record<string, unknown>
    inverse?: Record<string, unknown>
  },
  direction: 'undo' | 'redo',
) {
  if (entry.commandType !== 'geometry.params.set') return
  // undo：优先 inverse（apply inverse.after）；缺则用 payload.before
  const patch =
    direction === 'undo'
      ? (entry.inverse ??
        (entry.payload
          ? {
              path: entry.payload.path,
              before: entry.payload.after,
              after: entry.payload.before,
            }
          : undefined))
      : entry.payload
  if (!patch || typeof patch.path !== 'string') return
  const fullPath = patch.path as string
  const rawPath = fullPath.startsWith('acim.') ? fullPath.slice('acim.'.length) : fullPath
  const value = patch.after
  applyingHistory = true
  try {
    setAcimPath(rawPath, value)
  } finally {
    applyingHistory = false
  }
}

function onUndo() {
  const entry = history.undo()
  if (!entry) return
  applyGeometryEntry(entry, 'undo')
}

function onRedo() {
  const entry = history.redo()
  if (!entry) return
  applyGeometryEntry(entry, 'redo')
}

function onHistoryKeydown(e: KeyboardEvent) {
  const target = e.target as HTMLElement | null
  const tag = target?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable) {
    // 仍允许在表单控件上用快捷键（电机 CAD 常见）；若冲突可再收紧
  }
  const mod = e.metaKey || e.ctrlKey
  if (!mod) return
  const key = e.key.toLowerCase()
  if (key === 'z' && !e.shiftKey) {
    e.preventDefault()
    onUndo()
    return
  }
  if ((key === 'z' && e.shiftKey) || key === 'y') {
    e.preventDefault()
    onRedo()
  }
}

async function loadSample(key: SampleKey) {
  const opt = SAMPLE_OPTIONS.find((o) => o.key === key)
  if (!opt) return
  loadError.value = ''
  acimParams.value = null
  /**
   * fixture 切换：清空命令栈（跨样例不保留 undo）。
   * 空栈启动对齐 history/stack.json 缺文件策略。
   */
  history.clear()
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
  window.addEventListener('keydown', onHistoryKeydown)
  void loadSample(sampleKey.value)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onHistoryKeydown)
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
  margin: 4px 0 12px;
  color: var(--mo-text-muted);
  font-size: 11px;
  font-family: var(--mo-font-mono);
}

.history-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.history-meta {
  margin-left: auto;
  font-size: 11px;
  color: var(--mo-text-muted);
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
