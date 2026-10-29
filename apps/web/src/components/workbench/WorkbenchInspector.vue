<template>
  <aside class="inspector">
    <header class="inspector-head">
      <h2>{{ title }}</h2>
      <p v-if="session.rebuilding" class="hint">几何重建中…</p>
      <p v-else-if="session.geometryDirty" class="hint">几何参数已改，等待重建</p>
    </header>

    <div v-if="step === 'geometry'" class="pane">
      <p class="note">改参写入本会话，并在 {{ debounceMs }} ms 后 POST /geometry/rebuild。不自动求解。</p>
      <el-form label-position="top" size="small" class="form">
        <template v-if="isAf">
          <div class="pair">
            <el-form-item label="槽数 slotCount">
              <el-input-number :model-value="num('pmsm.slotCount')" :min="1" :step="1" controls-position="right" @change="onNum('pmsm.slotCount', $event)" />
            </el-form-item>
            <el-form-item label="极数 poleCount">
              <el-input-number :model-value="num('pmsm.poleCount')" :min="2" :step="2" controls-position="right" @change="onNum('pmsm.poleCount', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="磁钢厚度 mm">
              <el-input-number :model-value="num('pmsm.magnetThickness')" :min="0.05" :step="0.1" :precision="2" controls-position="right" @change="onNum('pmsm.magnetThickness', $event)" />
            </el-form-item>
            <el-form-item label="盘厚 diskThickness mm">
              <el-input-number :model-value="num('pmsm.diskThickness')" :min="0.1" :step="0.5" :precision="2" controls-position="right" @change="onNum('pmsm.diskThickness', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="盘数 diskCount">
              <el-input-number :model-value="num('pmsm.diskCount')" :min="1" :step="1" controls-position="right" @change="onNum('pmsm.diskCount', $event)" />
            </el-form-item>
            <el-form-item label="气隙 airgap mm">
              <el-input-number :model-value="num('pmsm.airgap')" :min="0.01" :step="0.1" :precision="2" controls-position="right" @change="onNum('pmsm.airgap', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="内径 mm">
              <el-input-number :model-value="num('pmsm.innerDiameter')" :min="0.1" :step="1" controls-position="right" @change="onNum('pmsm.innerDiameter', $event)" />
            </el-form-item>
            <el-form-item label="外径 mm">
              <el-input-number :model-value="num('pmsm.outerDiameter')" :min="0.1" :step="1" controls-position="right" @change="onNum('pmsm.outerDiameter', $event)" />
            </el-form-item>
          </div>
          <el-form-item label="磁钢扇区角 deg">
            <el-input-number :model-value="num('pmsm.magnetSectorAngle')" :min="1" :max="180" :step="1" controls-position="right" @change="onNum('pmsm.magnetSectorAngle', $event)" />
          </el-form-item>
        </template>
        <template v-else>
          <div class="pair">
            <el-form-item label="槽数 slotCount">
              <el-input-number :model-value="num('stator.slotCount')" :min="1" :step="1" controls-position="right" @change="onNum('stator.slotCount', $event)" />
            </el-form-item>
            <el-form-item label="极数 poleCount">
              <el-input-number :model-value="num('rotor.poleCount')" :min="2" :step="2" controls-position="right" @change="onNum('rotor.poleCount', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="磁钢厚度 mm">
              <el-input-number :model-value="num('rotor.magnetThickness')" :min="0.05" :step="0.1" :precision="2" controls-position="right" @change="onNum('rotor.magnetThickness', $event)" />
            </el-form-item>
            <el-form-item label="气隙 airgap mm">
              <el-input-number :model-value="num('airgap')" :min="0.01" :step="0.1" :precision="2" controls-position="right" @change="onNum('airgap', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="铁心长 stackLength mm">
              <el-input-number :model-value="num('stator.stackLength')" :min="0.1" :step="1" controls-position="right" @change="onNum('stator.stackLength', $event)" />
            </el-form-item>
            <el-form-item label="轴向有效长 mm">
              <el-input-number :model-value="num('axialActiveLength')" :min="0.1" :step="1" controls-position="right" @change="onNum('axialActiveLength', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="定子内径 mm">
              <el-input-number :model-value="num('stator.innerDiameter')" :min="0.1" :step="0.5" controls-position="right" @change="onNum('stator.innerDiameter', $event)" />
            </el-form-item>
            <el-form-item label="定子外径 mm">
              <el-input-number :model-value="num('stator.outerDiameter')" :min="0.1" :step="0.5" controls-position="right" @change="onNum('stator.outerDiameter', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="转子内径 mm">
              <el-input-number :model-value="num('rotor.innerDiameter')" :min="0.1" :step="0.5" controls-position="right" @change="onNum('rotor.innerDiameter', $event)" />
            </el-form-item>
            <el-form-item label="转子外径 mm">
              <el-input-number :model-value="num('rotor.outerDiameter')" :min="0.1" :step="0.5" controls-position="right" @change="onNum('rotor.outerDiameter', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="齿宽 mm">
              <el-input-number :model-value="num('stator.toothWidth')" :min="0.1" :step="0.1" :precision="2" controls-position="right" @change="onNum('stator.toothWidth', $event)" />
            </el-form-item>
            <el-form-item label="轭高 mm">
              <el-input-number :model-value="num('stator.yokeHeight')" :min="0.1" :step="0.1" :precision="2" controls-position="right" @change="onNum('stator.yokeHeight', $event)" />
            </el-form-item>
          </div>
        </template>

        <template v-if="session.projectMeta.machineType === 'ACIM'">
          <h3 class="sub">ACIM 导条（写入 geometry.params）</h3>
          <el-form-item label="导条槽形">
            <el-select :model-value="str('acim.barSlotShape')" style="width: 100%" @change="onStr('acim.barSlotShape', $event)">
              <el-option label="rectangular" value="rectangular" />
              <el-option label="oval" value="oval" />
              <el-option label="closed_slot" value="closed_slot" />
              <el-option label="open_slot" value="open_slot" />
            </el-select>
          </el-form-item>
          <div class="pair">
            <el-form-item label="导条宽 mm">
              <el-input-number :model-value="num('acim.barCrossSection.width')" :min="0.1" :step="0.5" controls-position="right" @change="onNum('acim.barCrossSection.width', $event)" />
            </el-form-item>
            <el-form-item label="导条高 mm">
              <el-input-number :model-value="num('acim.barCrossSection.height')" :min="0.1" :step="0.5" controls-position="right" @change="onNum('acim.barCrossSection.height', $event)" />
            </el-form-item>
          </div>
          <div class="pair">
            <el-form-item label="端环宽 mm">
              <el-input-number :model-value="num('acim.endRingSection.width')" :min="0.1" :step="0.5" controls-position="right" @change="onNum('acim.endRingSection.width', $event)" />
            </el-form-item>
            <el-form-item label="端环高 mm">
              <el-input-number :model-value="num('acim.endRingSection.height')" :min="0.1" :step="0.5" controls-position="right" @change="onNum('acim.endRingSection.height', $event)" />
            </el-form-item>
          </div>
          <el-form-item label="cagePolePairs">
            <el-input-number :model-value="num('acim.cagePolePairs')" :min="1" :step="1" controls-position="right" @change="onNum('acim.cagePolePairs', $event)" />
          </el-form-item>
        </template>
      </el-form>
    </div>

    <div v-else-if="step === 'materials'" class="pane">
      <p class="note">P0 占位：区域 → materialId，写入本会话材料切片。完整材料库步骤不在本门。</p>
      <p v-if="session.materialNote" class="hint">{{ session.materialNote }}</p>
      <el-form label-position="top" size="small" class="form">
        <el-form-item label="定子铁心 steel">
          <el-input :model-value="session.materials.regions.steel ?? ''" @change="onRegion('steel', $event)" />
        </el-form-item>
        <el-form-item v-if="session.projectMeta.machineType !== 'ACIM'" label="磁钢 magnet">
          <el-input :model-value="session.materials.regions.magnet ?? ''" @change="onRegion('magnet', $event)" />
        </el-form-item>
        <el-form-item label="绕组 conductor">
          <el-input :model-value="session.materials.regions.conductor ?? ''" @change="onRegion('conductor', $event)" />
        </el-form-item>
        <el-form-item v-if="session.projectMeta.machineType === 'ACIM'" label="导条 bar">
          <el-input :model-value="session.materials.regions.bar ?? ''" @change="onRegion('bar', $event)" />
        </el-form-item>
        <el-form-item v-if="session.projectMeta.machineType === 'ACIM'" label="端环 endRing">
          <el-input :model-value="session.materials.regions.endRing ?? ''" @change="onRegion('endRing', $event)" />
        </el-form-item>
        <el-form-item v-if="session.projectMeta.machineType !== 'ACIM'" label="br_t 覆盖">
          <el-input-number :model-value="session.materials.inline.br_t" :min="0.1" :max="1.6" :step="0.05" :precision="2" controls-position="right" @change="onInline('br_t', $event)" />
        </el-form-item>
        <el-form-item v-if="session.projectMeta.machineType === 'ACIM'" label="sigma_bar">
          <el-input-number :model-value="session.materials.inline.sigma_bar" :min="1" :step="1e6" controls-position="right" @change="onInline('sigma_bar', $event)" />
        </el-form-item>
      </el-form>
    </div>

    <div v-else-if="step === 'excitation'" class="pane">
      <p class="note">P0：工况写入本会话。可选驱动草稿不在此提交 Jobs。</p>
      <el-form label-position="top" size="small" class="form">
        <el-form-item label="转速 speed_rpm">
          <el-input-number :model-value="session.excitation.operatingPoint.speed_rpm" :min="0" :step="50" controls-position="right" @change="onOp('speed_rpm', $event)" />
        </el-form-item>
        <el-form-item v-if="session.projectMeta.machineType !== 'ACIM'" label="电流峰值 A">
          <el-input-number :model-value="session.excitation.operatingPoint.current_a_peak" :min="0" :step="1" controls-position="right" @change="onOp('current_a_peak', $event)" />
        </el-form-item>
        <el-form-item v-if="session.projectMeta.machineType === 'PMSM'" label="电流角 gamma_deg">
          <el-input-number :model-value="session.excitation.operatingPoint.gamma_deg" :min="-90" :max="90" :step="5" controls-position="right" @change="onOp('gamma_deg', $event)" />
        </el-form-item>
        <template v-if="session.projectMeta.machineType === 'ACIM'">
          <el-form-item label="电压峰值 V">
            <el-input-number :model-value="session.excitation.operatingPoint.voltage_v_peak" :min="0" :step="10" controls-position="right" @change="onOp('voltage_v_peak', $event)" />
          </el-form-item>
          <el-form-item label="频率 Hz">
            <el-input-number :model-value="session.excitation.operatingPoint.freq_hz" :min="1" :step="1" controls-position="right" @change="onOp('freq_hz', $event)" />
          </el-form-item>
          <el-form-item label="转差 slip（可选）">
            <el-input-number :model-value="session.excitation.operatingPoint.slip" :min="0.001" :max="0.5" :step="0.01" :precision="3" controls-position="right" @change="onOp('slip', $event)" />
          </el-form-item>
        </template>
        <el-form-item label="驱动草稿 mode">
          <el-select :model-value="session.excitation.driveDraft?.mode ?? ''" clearable style="width: 100%" @change="session.setDriveMode(String($event ?? ''))">
            <el-option label="bldc_square" value="bldc_square" />
            <el-option label="pmsm_foc" value="pmsm_foc" />
            <el-option label="acim_vf" value="acim_vf" />
            <el-option label="acim_foc" value="acim_foc" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <div v-else-if="step === 'mesh'" class="pane">
      <p class="mesh-warn">非网格生成完成 / not Maxwell mesh generation complete</p>
      <p class="note">只读 rebuild 描述符与 profile。这里不是 Maxwell 网格生成。</p>
      <dl class="meta">
        <div><dt>dataSource</dt><dd>{{ session.dataSource }}</dd></div>
        <div><dt>profile</dt><dd>{{ profile }}</dd></div>
        <div><dt>kind</dt><dd>{{ session.meshDescriptor?.kind ?? '—' }}</dd></div>
        <div><dt>primitives</dt><dd>{{ session.meshDescriptor?.primitives.length ?? 0 }}</dd></div>
        <div><dt>slotCount</dt><dd>{{ signals?.slotCount ?? '—' }}</dd></div>
        <div><dt>poleCount</dt><dd>{{ signals?.poleCount ?? '—' }}</dd></div>
        <div><dt>diskCount</dt><dd>{{ signals?.diskCount ?? '—' }}</dd></div>
        <div><dt>磁钢扇区数</dt><dd>{{ signals?.magnetCount ?? '—' }}</dd></div>
        <div><dt>磁钢径向厚 mm</dt><dd>{{ fmt(signals?.magnetBandMm) }}</dd></div>
        <div><dt>环高最大 mm</dt><dd>{{ fmt(signals?.maxRingHeightMm) }}</dd></div>
        <div><dt>paramsHash</dt><dd class="break">{{ session.paramsHash || '—' }}</dd></div>
        <div><dt>pipelineEntry</dt><dd>{{ session.pipelineEntry ? '有' : '无' }}</dd></div>
      </dl>
      <p v-if="session.rebuildError" class="warn">{{ session.rebuildError }}</p>
    </div>

    <div v-else-if="step === 'solve'" class="pane">
      <p class="note">显式求解。几何来自本会话 geometrySummary，不使用页面私有几何。解析 Jobs 不作为本步主路径。</p>
      <dl v-if="session.geometrySummary" class="meta">
        <div><dt>poles</dt><dd>{{ session.geometrySummary.poles }}</dd></div>
        <div><dt>slots</dt><dd>{{ session.geometrySummary.slots }}</dd></div>
        <div><dt>airgap_m</dt><dd>{{ fmt(session.geometrySummary.airgap_m, 6) }}</dd></div>
        <div><dt>stack_length_m</dt><dd>{{ fmt(session.geometrySummary.stack_length_m, 4) }}</dd></div>
        <div v-if="typeof session.geometrySummary.disk_thickness_m === 'number'">
          <dt>disk_thickness_m</dt><dd>{{ fmt(session.geometrySummary.disk_thickness_m, 4) }}</dd>
        </div>
        <div v-if="typeof session.geometrySummary.magnet_thickness_m === 'number'">
          <dt>magnet_thickness_m</dt><dd>{{ fmt(session.geometrySummary.magnet_thickness_m, 4) }}</dd>
        </div>
      </dl>
      <p v-else class="warn">当前没有 live geometrySummary，不能把 fixture 当作求解几何。</p>
      <div class="actions">
        <el-button type="primary" :loading="session.solving" :disabled="!canSolve" @click="session.solveExplicit()">
          求解
        </el-button>
      </div>
      <p v-if="session.materialNote" class="hint">{{ session.materialNote }}</p>
      <p v-if="session.solveError" class="warn">{{ session.solveError }}</p>
      <p v-if="session.analytic && session.analyticStale" class="hint">几何或工况已变，结果可能过期。请再次求解。</p>
      <template v-if="session.analytic">
        <p v-if="degradedSolve" class="warn">解析降级 · {{ session.analytic.source || session.analytic.result.meta.source || 'fixture' }} · 非金标宣称</p>
        <p v-else class="hint">路径 {{ session.analytic.source || '—' }} · {{ session.analytic.result.meta.solver }}</p>
        <dl class="meta">
          <div><dt>转矩 N·m</dt><dd>{{ fmt(session.analytic.result.torque_nm, 3) }}</dd></div>
          <div><dt>反电势峰 V</dt><dd>{{ fmt(session.analytic.result.back_emf_v_peak, 2) }}</dd></div>
          <div><dt>铜耗 W</dt><dd>{{ fmt(session.analytic.result.losses_w.copper, 2) }}</dd></div>
          <div><dt>铁耗 W</dt><dd>{{ fmt(session.analytic.result.losses_w.iron, 2) }}</dd></div>
          <div><dt>mock</dt><dd>{{ String(session.analytic.result.meta.mock) }}</dd></div>
        </dl>
      </template>
    </div>

    <div v-else class="pane">
      <p class="note">场图主路径仍是 Jobs artifacts。无 jobId 时不在本壳加载场图 fixture 当作结果。</p>
      <el-form label-position="top" size="small" class="form">
        <el-form-item label="lastFemJobId">
          <el-input v-model="jobDraft" placeholder="FEM job id" />
        </el-form-item>
      </el-form>
      <div class="actions">
        <el-button type="primary" :disabled="!jobDraft.trim()" @click="emit('open-field', jobDraft.trim())">
          在本壳查看场图
        </el-button>
      </div>
      <p v-if="session.analytic" class="hint">
        解析指针 {{ session.resultsRefs.analyticSource || '—' }}
        <span v-if="session.analyticStale"> · 结果可能过期</span>
      </p>
      <p v-else class="hint">尚无本会话解析结果。</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { descriptorSignals } from '@/lib/descriptorSignals'
import { REBUILD_DEBOUNCE_MS } from '@/lib/geometryRebuild'
import { getPath } from '@/lib/paramPath'
import { useProjectSession } from '@/stores/projectSession'
import type { UemMaterialRegions } from '@/lib/geometryDefaults'
import type { OperatingPoint } from '@/types/solver'

const props = defineProps<{
  step: 'geometry' | 'materials' | 'excitation' | 'mesh' | 'solve' | 'post'
}>()

const emit = defineEmits<{
  'open-field': [jobId: string]
}>()

const session = useProjectSession()
const debounceMs = REBUILD_DEBOUNCE_MS
const jobDraft = ref(session.resultsRefs.lastJobId)

watch(
  () => session.resultsRefs.lastJobId,
  (id) => {
    if (id && !jobDraft.value) jobDraft.value = id
  },
)

const isAf = computed(() => session.projectMeta.topology === 'AF')

const title = computed(() => {
  const map = {
    geometry: '几何',
    materials: '材料',
    excitation: '激励',
    mesh: '网格',
    solve: '求解',
    post: '后处理',
  }
  return map[props.step]
})

const signals = computed(() => descriptorSignals(session.meshDescriptor))

const profile = computed(() => {
  const d = session.meshDescriptor
  if (!d) return '—'
  const slot = d.meta.slotCount ?? '—'
  const pole = d.meta.poleCount ?? '—'
  return `${d.kind}/${session.machineLabel}/slots=${slot}/poles=${pole}`
})

const canSolve = computed(
  () =>
    session.phase === 'ready' &&
    session.dataSource === 'live' &&
    !!session.geometrySummary &&
    !session.geometryDirty &&
    !session.rebuilding &&
    !session.solving,
)

const degradedSolve = computed(() => {
  const src = session.analytic?.source ?? session.analytic?.result.meta.source
  return src === 'fixture' || src === 'mock' || session.analytic?.result.meta.mock === true
})

function num(path: string): number | undefined {
  const value = getPath(session.geometryParams, path)
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined
}

function str(path: string): string {
  const value = getPath(session.geometryParams, path)
  return typeof value === 'string' ? value : ''
}

function onNum(path: string, value: number | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return
  session.commitParam(path, value)
}

function onStr(path: string, value: string) {
  session.commitParam(path, value)
}

function onRegion(key: keyof UemMaterialRegions, value: string) {
  session.commitRegion(key, value)
}

function onInline(key: 'br_t' | 'sigma_bar', value: number | undefined) {
  session.commitInline(key, value)
}

function onOp(key: keyof OperatingPoint, value: number | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return
  session.commitOperatingPoint({ [key]: value })
}

function fmt(value: number | null | undefined, digits = 2): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—'
  return value.toFixed(digits)
}
</script>

<style scoped>
.inspector {
  width: 340px;
  flex-shrink: 0;
  border-left: 1px solid var(--mo-border);
  background: var(--mo-bg-panel);
  overflow: auto;
  min-height: 0;
}

.inspector-head {
  padding: 14px 14px 0;
}

.inspector-head h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.pane {
  padding: 10px 14px 18px;
}

.note,
.hint {
  margin: 6px 0 10px;
  color: var(--mo-text-muted);
  font-size: 11px;
}

.mesh-warn,
.warn {
  margin: 0 0 8px;
  color: var(--mo-amber);
  font-size: 12px;
}

.form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.form :deep(.el-input-number) {
  width: 100%;
}

.pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.sub {
  margin: 8px 0;
  font-size: 12px;
  color: var(--mo-amber);
}

.meta {
  margin: 0 0 10px;
}

.meta div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 3px 0;
  font-size: 12px;
}

.meta dt {
  color: var(--mo-text-muted);
}

.meta dd {
  margin: 0;
  font-family: var(--mo-font-mono);
  text-align: right;
}

.break {
  word-break: break-all;
}

.actions {
  margin: 8px 0;
}
</style>
