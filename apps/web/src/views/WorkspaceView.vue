<template>
  <div class="workbench">
    <div v-if="session.phase === 'loading'" class="banner banner-wait">正在打开工程会话…</div>
    <div v-else-if="session.dataSource !== 'live'" class="banner" role="status">
      <strong>样例/fixture · 非建模完成</strong>
      <span v-if="session.fixtureReason"> · {{ session.fixtureReason }}</span>
      <span v-if="session.rebuilding"> · 重建中…</span>
    </div>
    <div v-else class="banner banner-live" role="status">
      live · POST /geometry/rebuild
      <span v-if="session.paramsHash"> · paramsHash {{ shortHash }}</span>
      <span v-if="session.rebuilding"> · 重建中…</span>
    </div>

    <div class="workbench-body">
      <aside class="tree">
        <p class="kicker">一站式工作台</p>
        <h1>{{ session.projectMeta.name || '未命名工程' }}</h1>
        <p class="meta">
          <span v-if="session.projectMeta.projectId">{{ session.projectMeta.projectId }}</span>
          <span v-else>无 projectId · 本会话默认参数</span>
        </p>

        <label class="field-label">机型</label>
        <el-select
          :model-value="session.machineLabel"
          :disabled="session.phase !== 'ready'"
          size="small"
          style="width: 100%"
          @change="onMachine"
        >
          <el-option v-for="opt in machines" :key="opt.key" :label="opt.label" :value="opt.key" />
        </el-select>

        <div class="history-bar">
          <el-button size="small" :disabled="session.phase !== 'ready' || !session.canUndo" @click="session.undo()">撤销</el-button>
          <el-button size="small" :disabled="session.phase !== 'ready' || !session.canRedo" @click="session.redo()">重做</el-button>
          <span class="history-meta">{{ session.historyCursor }}/{{ session.historyLength }}</span>
        </div>

        <ol class="steps">
          <li v-for="(item, index) in steps" :key="item.id">
            <button
              type="button"
              class="step"
              :class="{ 'is-active': step === item.id }"
              @click="goStep(item.id)"
            >
              <span class="idx">{{ index + 1 }}</span>
              {{ item.label }}
            </button>
          </li>
        </ol>
        <p class="foot">经典链在本壳内切换。旧地址会回到这里，并带上同一 projectId。</p>
      </aside>

      <div v-if="showField" class="field-host">
        <div class="field-bar">
          <span>场图 · Jobs artifacts · {{ jobId }}</span>
          <el-button size="small" @click="clearJob">收起场图</el-button>
        </div>
        <FieldVizView />
      </div>

      <template v-else>
        <section class="viewport">
          <div class="hud">
            <span>{{ hudSource }}</span>
            <span v-if="signals">prims {{ signals.primitives }}</span>
            <span v-if="signals">slots {{ signals.slotCount ?? '—' }}</span>
            <span v-if="signals">poles {{ signals.poleCount ?? '—' }}</span>
            <span v-if="signals?.magnetBandMm != null">mag {{ signals.magnetBandMm.toFixed(2) }} mm</span>
            <span v-if="signals?.maxRingHeightMm != null">ring {{ signals.maxRingHeightMm.toFixed(2) }} mm</span>
          </div>
          <Viewport3D :key="session.viewportRev" :descriptor="session.meshDescriptor" />
        </section>
        <WorkbenchInspector v-if="session.phase === 'ready'" :step="step" @open-field="openField" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Viewport3D from '@/components/Viewport3D.vue'
import WorkbenchInspector from '@/components/workbench/WorkbenchInspector.vue'
import FieldVizView from '@/views/FieldVizView.vue'
import { descriptorSignals } from '@/lib/descriptorSignals'
import { SESSION_MACHINES } from '@/lib/geometryDefaults'
import { useProjectSession } from '@/stores/projectSession'
import type { MachineType, Topology } from '@/api/types'

const STEPS = [
  { id: 'geometry', label: '几何' },
  { id: 'materials', label: '材料' },
  { id: 'excitation', label: '激励' },
  { id: 'mesh', label: '网格' },
  { id: 'solve', label: '求解' },
  { id: 'post', label: '后处理' },
] as const

type StepId = (typeof STEPS)[number]['id']

const route = useRoute()
const router = useRouter()
const session = useProjectSession()
const machines = SESSION_MACHINES
const steps = STEPS

function queryText(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function parseStep(value: unknown): StepId {
  const text = queryText(value)
  return STEPS.some((item) => item.id === text) ? (text as StepId) : 'geometry'
}

const step = computed(() => parseStep(route.query.step))
const jobId = computed(() => queryText(route.query.jobId))
const showField = computed(() => step.value === 'post' && jobId.value.length > 0)
const signals = computed(() => descriptorSignals(session.meshDescriptor))
const shortHash = computed(() =>
  session.paramsHash.length > 12 ? `${session.paramsHash.slice(0, 12)}…` : session.paramsHash,
)
const hudSource = computed(() =>
  session.dataSource === 'live' ? 'live · rebuild' : '样例/fixture · 非建模完成',
)

function hydrateKey(): string {
  return [
    queryText(route.query.projectId),
    queryText(route.query.source),
    queryText(route.query.topology),
    queryText(route.query.machineType),
  ].join('|')
}

watch(
  hydrateKey,
  () => {
    void session.hydrate({
      projectId: queryText(route.query.projectId),
      source: queryText(route.query.source),
      topology: queryText(route.query.topology),
      machineType: queryText(route.query.machineType),
      jobId: queryText(route.query.jobId),
    })
  },
  { immediate: true },
)

watch(jobId, (id) => session.noteFemJob(id))

function goStep(next: StepId) {
  void router.replace({ query: { ...route.query, step: next } })
}

function onMachine(key: string) {
  const found = machines.find((item) => item.key === key)
  if (!found) return
  session.setMachine(found.topology as Topology, found.machineType as MachineType)
}

function openField(id: string) {
  session.noteFemJob(id)
  void router.replace({ query: { ...route.query, step: 'post', jobId: id } })
}

function clearJob() {
  const next = { ...route.query }
  delete next.jobId
  void router.replace({ query: next })
}

function onHistoryKeydown(event: KeyboardEvent) {
  const mod = event.metaKey || event.ctrlKey
  if (!mod) return
  const key = event.key.toLowerCase()
  if (key === 'z' && !event.shiftKey) {
    event.preventDefault()
    session.undo()
    return
  }
  if ((key === 'z' && event.shiftKey) || key === 'y') {
    event.preventDefault()
    session.redo()
  }
}

onMounted(() => window.addEventListener('keydown', onHistoryKeydown))
onUnmounted(() => window.removeEventListener('keydown', onHistoryKeydown))
</script>

<style scoped>
.workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.banner {
  flex-shrink: 0;
  padding: 8px 14px;
  background: rgba(245, 158, 11, 0.16);
  color: var(--mo-amber);
  border-bottom: 1px solid rgba(245, 158, 11, 0.4);
  font-size: 12px;
}

.banner-live {
  background: rgba(45, 212, 191, 0.1);
  color: var(--mo-accent);
  border-bottom-color: rgba(45, 212, 191, 0.35);
}

.banner-wait {
  background: var(--mo-bg-elevated);
  color: var(--mo-text-secondary);
  border-bottom: 1px solid var(--mo-border);
}

.workbench-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.tree {
  width: 232px;
  flex-shrink: 0;
  padding: 14px 12px;
  border-right: 1px solid var(--mo-border);
  background: var(--mo-bg-panel);
  overflow: auto;
}

.kicker {
  margin: 0;
  color: var(--mo-text-muted);
  font-size: 11px;
}

.tree h1 {
  margin: 4px 0;
  font-size: 15px;
  font-weight: 600;
}

.meta,
.foot,
.field-label {
  color: var(--mo-text-muted);
  font-size: 11px;
}

.meta {
  margin: 0 0 12px;
  font-family: var(--mo-font-mono);
  word-break: break-all;
}

.field-label {
  display: block;
  margin-bottom: 4px;
}

.history-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 12px 0;
}

.history-meta {
  margin-left: auto;
  font-family: var(--mo-font-mono);
  font-size: 11px;
  color: var(--mo-text-muted);
}

.steps {
  list-style: none;
  margin: 0;
  padding: 0;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin: 2px 0;
  padding: 7px 8px;
  border: 0;
  border-radius: var(--mo-radius-sm);
  background: transparent;
  color: var(--mo-text-secondary);
  cursor: pointer;
  text-align: left;
}

.step:hover {
  background: var(--mo-bg-hover);
  color: var(--mo-text-primary);
}

.step.is-active {
  background: var(--mo-accent-dim);
  color: var(--mo-accent);
}

.idx {
  width: 16px;
  font-family: var(--mo-font-mono);
  font-size: 11px;
}

.foot {
  margin: 14px 0 0;
}

.viewport {
  position: relative;
  flex: 1;
  min-width: 0;
  min-height: 0;
}

.hud {
  position: absolute;
  z-index: 2;
  top: 8px;
  left: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: calc(100% - 16px);
  padding: 4px 8px;
  border-radius: var(--mo-radius);
  background: rgba(14, 15, 17, 0.82);
  color: var(--mo-text-secondary);
  font-family: var(--mo-font-mono);
  font-size: 11px;
  pointer-events: none;
}

.field-host {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.field-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--mo-border);
  color: var(--mo-text-secondary);
  font-size: 12px;
}

.field-host :deep(.field-viz) {
  flex: 1;
  min-height: 0;
  height: auto;
}
</style>
