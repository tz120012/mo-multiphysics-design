<template>
  <div class="field-viz" :data-field-source="loading ? 'loading' : dataSource">
    <aside class="field-side">
      <h2 class="side-title">场量 · 精简可视化</h2>
      <p class="side-desc">
        Q3-6 · F1 §5 · <span data-field-source-label>source={{ loading ? '…' : dataSource }}</span> · {{ artifactBase }}
      </p>

      <dl v-if="queryJobId || queryResultRef || job" class="meta-list job-meta">
        <div v-if="queryJobId || job" class="meta-row">
          <dt>jobId</dt>
          <dd class="mono-trunc" :title="(job?.id || queryJobId) || ''">{{ shortId(job?.id || queryJobId || '') }}</dd>
        </div>
        <div v-if="job" class="meta-row">
          <dt>job.status</dt>
          <dd>
            <span class="status-pill" :data-status="job.status">{{ job.status }}</span>
          </dd>
        </div>
        <div v-if="displayResultRef" class="meta-row">
          <dt>resultRef</dt>
          <dd class="mono-trunc" :title="displayResultRef">{{ displayResultRef }}</dd>
        </div>
        <div v-if="queryProjectId" class="meta-row">
          <dt>projectId</dt>
          <dd class="mono-trunc" :title="queryProjectId">{{ shortId(queryProjectId) }}</dd>
        </div>
        <div class="meta-row">
          <dt>source</dt>
          <dd>{{ loading ? '…' : dataSource }}</dd>
        </div>
      </dl>

      <div v-if="jobError" class="error-box">{{ jobError }}</div>
      <div v-if="loadError" class="error-box">{{ loadError }}</div>
      <p v-if="loading" class="degrade-note">{{ loadingHint }}</p>
      <p v-else :class="dataSource === 'job-artifacts' ? 'live-note' : 'degrade-note'">
        {{ sourceHint }}
      </p>

      <section
        v-if="postprocessView"
        class="post-panel"
        :data-postprocess-kind="postprocessView.kind"
        :data-equation-mode="postprocessView.equationMode"
        :data-pending-calibration="postprocessView.pendingCalibration ? 'true' : 'false'"
        :data-magnetostatic-path-ready="postprocessView.pathReadyText"
      >
        <div class="post-head">
          <h3 class="post-title">{{ postprocessView.title }}</h3>
          <span
            v-if="postprocessView.pendingCalibration"
            class="cal-badge"
            data-pending-calibration
          >pending_calibration</span>
        </div>
        <p class="post-status">
          equationMode={{ postprocessView.equationModeText }}
          · magnetostaticPathReady={{ postprocessView.pathReadyText }}
        </p>
        <p class="post-note">{{ postprocessView.note }}</p>
        <dl class="meta-list post-list">
          <div
            v-for="row in postprocessView.rows"
            :key="row.key"
            class="meta-row"
            :data-scalar="row.key"
            :data-scalar-state="row.state"
            :data-uncalibrated="row.uncalibrated ? 'true' : 'false'"
          >
            <dt>{{ row.key }}</dt>
            <dd>
              <span class="scalar-value">{{ row.value }}</span>
              <span v-if="row.unit" class="scalar-unit">{{ row.unit }}</span>
              <span v-if="row.uncalibrated" class="cal-badge cal-badge-inline">pending_calibration</span>
            </dd>
          </div>
        </dl>
      </section>

      <template v-if="manifest">
        <dl class="meta-list">
          <div class="meta-row"><dt>manifest.jobId</dt><dd class="mono-trunc" :title="manifest.jobId">{{ shortId(manifest.jobId) }}</dd></div>
          <div class="meta-row"><dt>status</dt><dd>{{ manifest.status }}</dd></div>
          <div class="meta-row"><dt>kernel</dt><dd>{{ manifest.solverKernel }}</dd></div>
          <div class="meta-row"><dt>topo×type</dt><dd>{{ manifest.topology }} · {{ manifest.machineType }}</dd></div>
          <div class="meta-row"><dt>dim</dt><dd>{{ manifest.dim }}</dd></div>
          <div class="meta-row"><dt>artifacts</dt><dd>{{ manifest.artifacts.length }}</dd></div>
        </dl>

        <h3 class="section-title">manifest.scalars</h3>
        <el-table :data="manifestScalarRows" size="small" stripe empty-text="—" style="width: 100%">
          <el-table-column prop="key" label="键" min-width="100" />
          <el-table-column prop="value" label="值" min-width="100" />
        </el-table>
      </template>

      <template v-if="artifactRows.length">
        <h3 class="section-title">artifacts</h3>
        <ul class="art-list">
          <li v-for="(a, i) in artifactRows" :key="`${a.role}-${a.path}-${i}`">
            <span class="art-role">{{ a.role }}</span>
            <span class="art-fmt">{{ a.format }}</span>
            <span class="art-path" :title="a.path">{{ basename(a.path) }}</span>
          </li>
        </ul>
      </template>

      <h3 v-if="scalarsArtifact" class="section-title">scalars.json</h3>
      <el-table
        v-if="scalarsArtifact"
        :data="artifactScalarRows"
        size="small"
        stripe
        empty-text="—"
        style="width: 100%"
      >
        <el-table-column prop="key" label="键" min-width="100" />
        <el-table-column prop="value" label="值" min-width="100" />
      </el-table>

      <div v-if="previewUrl" class="preview-block">
        <h3 class="section-title">preview</h3>
        <img :src="previewUrl" alt="FEM preview" class="preview-img" />
      </div>

      <p class="hint">
        仅消费精简 JSON / glTF / PNG（docs/drafts/Q3-轴向与FEM边界.md §5）。禁止默认 VTK/全场。不宣称误差达标，不宣称 MVP。
      </p>
    </aside>

    <section class="field-main">
      <div ref="hostRef" class="gltf-host" />
      <p v-if="gltfError" class="error-box">{{ gltfError }}</p>
      <p v-else-if="!meshLoaded" class="empty-hint">加载 slice/surface glTF…</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import {
  FEM_MANIFEST_FIXTURE_BASE,
  type FemArtifact,
  type FemArtifactFormat,
  type FemArtifactRole,
  type FemDim,
  type FemJobStatus,
  type FemManifest,
  type FemScalarsArtifact,
  type FemSolverKernel,
} from '@/types/fieldViz'
import { buildFieldPostprocessView, assignManifestPostprocessFields } from '@/lib/fieldPostprocess'
import { disposeObject3D } from '@/lib/meshToThree'
import {
  getJob,
  getJobArtifact,
  getJobArtifactBlob,
  listJobArtifacts,
  pollJob,
  JobPollAbortedError,
  JobPollTimeoutError,
  type JobArtifactsList,
} from '@/api/jobs'
import { isJobTerminal, type Job } from '@/api/types'

const route = useRoute()

const queryJobId = computed(() =>
  typeof route.query.jobId === 'string' ? route.query.jobId.trim() : '',
)
const queryResultRef = computed(() =>
  typeof route.query.resultRef === 'string' ? route.query.resultRef.trim() : '',
)
const queryProjectId = computed(() =>
  typeof route.query.projectId === 'string' ? route.query.projectId.trim() : '',
)
/** 显式 `?source=fixture`：联调/演示强制 public fixture，跳过 artifacts list/get。 */
const forceFixture = computed(() => {
  const raw = route.query.source
  const text = typeof raw === 'string' ? raw : Array.isArray(raw) ? raw[0] : ''
  return (text || '').trim().toLowerCase() === 'fixture'
})

/**
 * `/field` 数据源（Q4+-3 L2，docs/drafts/Q4+-3-mems单文件与artifacts收口.md §2）。
 *
 * 1. `?source=fixture`（大小写不敏感）：强制 public fixture，不请求 Jobs artifacts。
 *    无 jobId → `fixture`；有 jobId → `job-fixture`。
 * 2. 无 jobId：`fixture`（`FEM_MANIFEST_FIXTURE_BASE`）。
 * 3. 有 jobId：`GET /api/v1/jobs/{id}/artifacts`，再 GET `.../artifacts/{path}`
 *    （manifest / scalars / slice|surface / preview）。
 *    列表非空，或上述关键 GET 成功 → `job-artifacts`（页眉 `source=` 可见）。
 * 4. `job-fixture` 仅当列表失败或为空，且 manifest 与 scalars/slice/preview 均 404 或不可达。
 *    列表非空时，单文件失败仍保持 `job-artifacts`，不改吃 fixture。
 * 5. 不走 mems 整包，也不调用 mems/files（Q4+-3b / F5-A）。
 *    状态注记只写「不宣称误差达标」；不宣称 MVP，不写精度达标。
 * 6. 后处理面板只读已取到的 scalars / manifest（FEM tip 797ce67）。
 *    equationMode=magnetostatic 或 magnetostaticPathReady=true → 磁静力学后处理；
 *    heat_proxy 或缺省 → heat-proxy / 非磁静力学真值。不改上面的 source 规则。
 */
type FieldDataSource = 'fixture' | 'job-fixture' | 'job-artifacts'

const job = ref<Job | null>(null)
const jobError = ref<string | null>(null)
/** fixture：无 jobId。job-fixture：有 jobId 但未吃到精简件。job-artifacts：Jobs artifacts。 */
const dataSource = ref<FieldDataSource>('fixture')
const artifactBase = ref<string>(FEM_MANIFEST_FIXTURE_BASE)
const degradeReason = ref<string | null>(null)
const loading = ref(true)

const manifest = ref<FemManifest | null>(null)
const artifactRows = ref<FemArtifact[]>([])
const scalarsArtifact = ref<FemScalarsArtifact | null>(null)
const loadError = ref<string | null>(null)
const gltfError = ref<string | null>(null)
const meshLoaded = ref(false)
const previewUrl = ref<string | null>(null)
const hostRef = ref<HTMLDivElement | null>(null)

let jobAbort: AbortController | null = null
let objectUrls: string[] = []

const ROLES: readonly FemArtifactRole[] = ['scalars', 'surface', 'slice', 'preview', 'other']
const FORMATS: readonly FemArtifactFormat[] = ['json', 'gltf', 'glb', 'png', 'webp', 'other']
const MESH_FORMATS: readonly FemArtifactFormat[] = ['glb', 'gltf']
const STATUSES: readonly FemJobStatus[] = ['queued', 'running', 'succeeded', 'failed', 'cancelled']

const displayResultRef = computed(
  () => job.value?.resultRef || queryResultRef.value || '',
)

const loadingHint = computed(() =>
  forceFixture.value || !queryJobId.value ? '正在加载 dry-run fixture…' : '正在读取任务与精简产物…',
)

const sourceHint = computed(() => {
  if (dataSource.value === 'job-artifacts') {
    return '来源 job-artifacts：已请求 GET /jobs/{id}/artifacts 及单文件精简件。不宣称误差达标。'
  }
  if (dataSource.value === 'job-fixture') {
    const why = degradeReason.value ? `（${degradeReason.value}）` : ''
    return `已降级 public fixture${why}。当前场数据不是该 job 的精简产物。不宣称误差达标。`
  }
  const why = forceFixture.value ? '（显式 ?source=fixture）' : ''
  return `dry-run：未带 jobId，使用 public fixture${why}。不宣称误差达标。`
})

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let meshRoot: THREE.Object3D | null = null
let animId = 0
let resizeObserver: ResizeObserver | null = null

function basename(path: string): string {
  const parts = path.replace(/\\/g, '/').split('/')
  return parts[parts.length - 1] || path
}

function shortId(id: string): string {
  if (id.length <= 12) return id
  return `${id.slice(0, 8)}…`
}

/** manifest 内 path 多为 .mems 相对路径；fixture/降级用 basename 映射到 artifactBase */
function resolveArtifactUrl(artifact: FemArtifact): string {
  return `${artifactBase.value}/${basename(artifact.path)}`
}

function clipMessage(message: string): string {
  const one = message.replace(/\s+/g, ' ').trim()
  if (!one || one.startsWith('<')) return ''
  return one.length > 180 ? `${one.slice(0, 180)}…` : one
}

function errorMessage(e: unknown): string {
  if (axios.isAxiosError(e)) {
    const data = e.response?.data
    if (typeof data === 'string') {
      const text = clipMessage(data)
      if (text) return text
    }
    if (data && typeof data === 'object' && !(data instanceof Blob)) {
      const body = data as { message?: unknown; detail?: unknown }
      if (typeof body.message === 'string') {
        const text = clipMessage(body.message)
        if (text) return text
      }
      const detail = body.detail
      if (typeof detail === 'string') {
        const text = clipMessage(detail)
        if (text) return text
      }
      if (detail && typeof detail === 'object' && 'message' in detail) {
        const message = (detail as { message?: unknown }).message
        if (typeof message === 'string') {
          const text = clipMessage(message)
          if (text) return text
        }
      }
    }
    if (!e.response) return `API 不可达：${e.message}`
    if (e.response.status) return `HTTP ${e.response.status}`
    return e.message
  }
  return e instanceof Error ? e.message : String(e)
}

function isAbortError(e: unknown, signal?: AbortSignal): boolean {
  if (signal?.aborted) return true
  if (e instanceof JobPollAbortedError) return true
  if (e instanceof DOMException && e.name === 'AbortError') return true
  if (axios.isAxiosError(e) && (e.code === 'ERR_CANCELED' || e.name === 'CanceledError')) return true
  return false
}

function throwIfAborted(signal: AbortSignal) {
  if (signal.aborted) throw new DOMException('The operation was aborted', 'AbortError')
}

function stillCurrent(signal: AbortSignal): boolean {
  return !signal.aborted && jobAbort?.signal === signal
}

function revokeAllObjectUrls() {
  for (const url of objectUrls) URL.revokeObjectURL(url)
  objectUrls = []
}

function asRole(value: string): FemArtifactRole {
  return (ROLES as readonly string[]).includes(value) ? (value as FemArtifactRole) : 'other'
}

function asFormat(value: string): FemArtifactFormat {
  return (FORMATS as readonly string[]).includes(value) ? (value as FemArtifactFormat) : 'other'
}

function coerceArtifacts(
  raw: Array<{ path?: unknown; role?: unknown; format?: unknown; bytes?: unknown }>,
): FemArtifact[] {
  const out: FemArtifact[] = []
  for (const item of raw) {
    if (!item || typeof item.path !== 'string' || !item.path.trim()) continue
    if (typeof item.role !== 'string' || typeof item.format !== 'string') continue
    const art: FemArtifact = {
      path: item.path.trim(),
      role: asRole(item.role),
      format: asFormat(item.format),
    }
    if (typeof item.bytes === 'number' && Number.isFinite(item.bytes)) art.bytes = item.bytes
    out.push(art)
  }
  return out
}

function isKernel(value: unknown): value is FemSolverKernel {
  return value === 'elmer' || value === 'getdp'
}

function isDim(value: unknown): value is FemDim {
  return value === '2d' || value === '3d'
}

function coerceManifest(raw: unknown): FemManifest | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  if (typeof o.jobId !== 'string') return null
  if (typeof o.status !== 'string' || !(STATUSES as readonly string[]).includes(o.status)) return null
  if (!isKernel(o.solverKernel) || !isDim(o.dim)) return null
  if (o.topology !== 'RF' && o.topology !== 'AF') return null
  if (o.machineType !== 'BLDC' && o.machineType !== 'PMSM' && o.machineType !== 'ACIM') return null
  if (!o.scalars || typeof o.scalars !== 'object' || Array.isArray(o.scalars)) return null
  const artifacts = Array.isArray(o.artifacts)
    ? coerceArtifacts(o.artifacts as Array<{ path?: unknown; role?: unknown; format?: unknown; bytes?: unknown }>)
    : []
  const manifestDoc: FemManifest = {
    jobId: o.jobId,
    status: o.status as FemJobStatus,
    solverKernel: o.solverKernel,
    topology: o.topology,
    machineType: o.machineType,
    dim: o.dim,
    scalars: o.scalars as Record<string, unknown>,
    artifacts,
  }
  if (typeof o.createdAt === 'string') manifestDoc.createdAt = o.createdAt
  if (typeof o.updatedAt === 'string') manifestDoc.updatedAt = o.updatedAt
  assignManifestPostprocessFields(manifestDoc, o)
  return manifestDoc
}

function pickArtifact(
  arts: FemArtifact[],
  role: FemArtifactRole,
  formats: readonly FemArtifactFormat[],
): FemArtifact | undefined {
  return arts.find((a) => a.role === role && formats.includes(a.format))
}

function pickMeshArtifact(arts: FemArtifact[]): FemArtifact | undefined {
  return pickArtifact(arts, 'slice', MESH_FORMATS) ?? pickArtifact(arts, 'surface', MESH_FORMATS)
}

/** resultRef → 默认 manifest。列表为空时按序尝试，直到关键 GET 成功或全部 404/不可达。 */
function manifestPathCandidates(listed: JobArtifactsList | null, jobId: string): string[] {
  const raw = [
    listed?.resultRef,
    job.value?.resultRef,
    queryResultRef.value,
    `solver/fem/jobs/${jobId}/manifest.json`,
  ]
  const out: string[] = []
  const seen = new Set<string>()
  for (const candidate of raw) {
    const text = (candidate || '').trim().replace(/\\/g, '/').replace(/^\/+/, '')
    if (!text || text.split('/').includes('..')) continue
    if (seen.has(text)) continue
    seen.add(text)
    out.push(text)
  }
  if (out.length === 0) out.push(`solver/fem/jobs/${jobId}/manifest.json`)
  return out
}

function asScalars(value: unknown): FemScalarsArtifact | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return value as FemScalarsArtifact
}

async function fetchOptional<T>(run: () => Promise<T>, signal: AbortSignal): Promise<T | null> {
  try {
    return await run()
  } catch (e) {
    if (isAbortError(e, signal)) throw e
    return null
  }
}

function flattenScalars(obj: Record<string, unknown>, prefix = ''): { key: string; value: string }[] {
  const rows: { key: string; value: string }[] = []
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v != null && typeof v === 'object' && !Array.isArray(v)) {
      rows.push(...flattenScalars(v as Record<string, unknown>, key))
    } else {
      rows.push({ key, value: v === undefined ? '—' : String(v) })
    }
  }
  return rows
}

const manifestScalarRows = computed(() =>
  manifest.value ? flattenScalars(manifest.value.scalars as Record<string, unknown>) : [],
)

const artifactScalarRows = computed(() =>
  scalarsArtifact.value
    ? flattenScalars(scalarsArtifact.value as Record<string, unknown>)
    : [],
)

const postprocessView = computed(() =>
  buildFieldPostprocessView(manifest.value, scalarsArtifact.value),
)

function clearMesh() {
  if (!scene || !meshRoot) return
  scene.remove(meshRoot)
  disposeObject3D(meshRoot)
  meshRoot = null
}

function fitCamera(object: THREE.Object3D) {
  if (!camera || !controls) return
  const box = new THREE.Box3().setFromObject(object)
  if (box.isEmpty()) return
  const size = box.getSize(new THREE.Vector3())
  const center = box.getCenter(new THREE.Vector3())
  const maxDim = Math.max(size.x, size.y, size.z, 1e-4)
  const dist = maxDim * 2.4
  camera.near = Math.max(dist / 200, 1e-4)
  camera.far = dist * 50
  camera.position.set(center.x + dist * 0.7, center.y + dist * 0.55, center.z + dist * 0.9)
  camera.lookAt(center)
  camera.updateProjectionMatrix()
  controls.target.copy(center)
  controls.update()
}

function handleResize() {
  const host = hostRef.value
  if (!host || !renderer || !camera) return
  const w = host.clientWidth || 1
  const h = host.clientHeight || 1
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h, false)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
}

function animate() {
  animId = requestAnimationFrame(animate)
  controls?.update()
  if (renderer && scene && camera) renderer.render(scene, camera)
}

function initScene() {
  const host = hostRef.value
  if (!host) return
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0e0f11)
  const w = host.clientWidth || 1
  const h = host.clientHeight || 1
  camera = new THREE.PerspectiveCamera(45, w / h, 0.001, 100)
  camera.position.set(1.2, 1.0, 1.4)
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(w, h, false)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  host.appendChild(renderer.domElement)
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  scene.add(new THREE.AmbientLight(0xffffff, 0.6))
  const key = new THREE.DirectionalLight(0xffffff, 0.85)
  key.position.set(2, 3, 4)
  scene.add(key)
  scene.add(new THREE.AxesHelper(0.5))
  const grid = new THREE.GridHelper(2, 10, 0x2a2d34, 0x1f2228)
  grid.rotation.x = Math.PI / 2
  scene.add(grid)
  resizeObserver = new ResizeObserver(() => handleResize())
  resizeObserver.observe(host)
  window.addEventListener('resize', handleResize)
  animate()
}

function teardownScene() {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
  resizeObserver = null
  clearMesh()
  controls?.dispose()
  controls = null
  if (renderer) {
    renderer.dispose()
    renderer.domElement.remove()
    renderer = null
  }
  scene = null
  camera = null
}

function resetViz() {
  manifest.value = null
  scalarsArtifact.value = null
  artifactRows.value = []
  previewUrl.value = null
  meshLoaded.value = false
  gltfError.value = null
  loadError.value = null
  revokeAllObjectUrls()
  clearMesh()
}

function attachMesh(root: THREE.Object3D) {
  if (!scene) return
  clearMesh()
  meshRoot = root
  meshRoot.traverse((obj) => {
    const mesh = obj as THREE.Mesh
    if (mesh.isMesh) {
      const mat = mesh.material as THREE.MeshStandardMaterial
      if (mat && 'metalness' in mat) {
        mat.metalness = 0.2
        mat.roughness = 0.55
        mat.side = THREE.DoubleSide
      }
    }
  })
  scene.add(meshRoot)
  fitCamera(meshRoot)
  meshLoaded.value = true
}

async function loadGltf(url: string, signal: AbortSignal) {
  if (!scene || signal.aborted) return
  clearMesh()
  gltfError.value = null
  meshLoaded.value = false
  const loader = new GLTFLoader()
  try {
    const gltf = await loader.loadAsync(url)
    if (signal.aborted || !scene) {
      disposeObject3D(gltf.scene)
      throwIfAborted(signal)
      return
    }
    attachMesh(gltf.scene)
  } catch (e) {
    if (isAbortError(e, signal)) throw e
    gltfError.value = e instanceof Error ? e.message : String(e)
  }
}

async function loadGltfBytes(data: ArrayBuffer, signal: AbortSignal) {
  if (!scene || signal.aborted) return
  clearMesh()
  gltfError.value = null
  meshLoaded.value = false
  const loader = new GLTFLoader()
  try {
    const gltf = await loader.parseAsync(data, '')
    if (signal.aborted || !scene) {
      disposeObject3D(gltf.scene)
      throwIfAborted(signal)
      return
    }
    attachMesh(gltf.scene)
  } catch (e) {
    if (isAbortError(e, signal)) throw e
    gltfError.value = e instanceof Error ? e.message : String(e)
  }
}

/**
 * public fixture：manifest → scalars / slice|surface / preview。
 * 仅无 jobId、显式 ?source=fixture，或列表空/失败且关键 GET 404/不可达时进入。
 */
async function loadFromBase(base: string, source: 'fixture' | 'job-fixture', signal: AbortSignal) {
  throwIfAborted(signal)
  resetViz()
  artifactBase.value = base
  dataSource.value = source
  try {
    const res = await fetch(`${base}/manifest.json`, { signal })
    throwIfAborted(signal)
    if (!res.ok) throw new Error(`manifest ${res.status}`)
    const m = coerceManifest(await res.json())
    if (!m) throw new Error('fixture manifest 形状无效')
    manifest.value = m
    artifactRows.value = m.artifacts

    const scalarsArt = pickArtifact(m.artifacts, 'scalars', ['json'])
    if (scalarsArt) {
      const sRes = await fetch(resolveArtifactUrl(scalarsArt), { signal })
      throwIfAborted(signal)
      if (sRes.ok) scalarsArtifact.value = asScalars(await sRes.json())
    }

    const previewArt = pickArtifact(m.artifacts, 'preview', ['png', 'webp'])
    previewUrl.value = previewArt ? resolveArtifactUrl(previewArt) : null

    const meshArt = pickMeshArtifact(m.artifacts)
    if (meshArt) {
      await loadGltf(resolveArtifactUrl(meshArt), signal)
    } else if (stillCurrent(signal)) {
      gltfError.value = 'manifest 无 slice/surface glTF/GLB 产物'
    }
  } catch (e) {
    if (isAbortError(e, signal)) throw e
    loadError.value = e instanceof Error ? e.message : String(e)
  }
}

async function loadFixtureDegraded(signal: AbortSignal) {
  throwIfAborted(signal)
  const src: 'fixture' | 'job-fixture' = queryJobId.value || job.value ? 'job-fixture' : 'fixture'
  await loadFromBase(FEM_MANIFEST_FIXTURE_BASE, src, signal)
}

function listFailReason(e: unknown): string {
  if (axios.isAxiosError(e) && e.response?.status === 404) {
    const msg = errorMessage(e)
    if (!msg || msg === 'Not Found' || msg === 'HTTP 404') {
      return '产物列表 404（路由未就绪或无 manifest）'
    }
    return `产物列表 404：${msg}`
  }
  if (axios.isAxiosError(e) && !e.response) return '产物列表不可达'
  return `产物列表失败：${errorMessage(e)}`
}

/** 列表空/失败时，须关键 GET 也 404 或不可达才允许降级 fixture。 */
function emptyDegradeReason(listError: unknown, manifestError: unknown): string {
  const listPart = listError ? listFailReason(listError) : '产物列表为空'
  if (!manifestError) return `${listPart}，且关键 GET 未取到`
  if (axios.isAxiosError(manifestError) && !manifestError.response) {
    return `${listPart}，且 manifest GET 不可达`
  }
  if (axios.isAxiosError(manifestError) && manifestError.response?.status === 404) {
    return `${listPart}，且 manifest GET 404`
  }
  return `${listPart}，且 manifest GET 失败：${errorMessage(manifestError)}`
}

/**
 * F1 / Q4+-3：list → manifest（resultRef 或默认路径）→ scalars / slice|surface / preview。
 * 返回 false 仅当列表失败或为空，且关键 GET 均 404/不可达。
 * 列表非空时即使单文件失败也保持 job-artifacts。
 */
async function tryLoadJobArtifacts(jobId: string, signal: AbortSignal): Promise<boolean> {
  let listed: JobArtifactsList | null = null
  let listError: unknown = null
  try {
    listed = await listJobArtifacts(jobId, signal)
  } catch (e) {
    if (isAbortError(e, signal)) throw e
    listError = e
  }
  if (!stillCurrent(signal)) return false

  if (listed?.resultRef && job.value && !job.value.resultRef) {
    job.value = { ...job.value, resultRef: listed.resultRef }
  }

  const listedArts = listed
    ? coerceArtifacts(Array.isArray(listed.artifacts) ? listed.artifacts : [])
    : []

  const candidates = manifestPathCandidates(listed, jobId)
  const toTry = listedArts.length > 0 ? candidates.slice(0, 1) : candidates
  let manifestObj: FemManifest | null = null
  let manifestError: unknown = null
  for (const path of toTry) {
    try {
      const raw = await getJobArtifact(jobId, path, signal)
      if (!stillCurrent(signal)) return false
      const parsed = coerceManifest(raw)
      if (parsed) {
        manifestObj = parsed
        manifestError = null
        break
      }
      manifestError = new Error('manifest 形状无效')
    } catch (e) {
      if (isAbortError(e, signal)) throw e
      manifestError = e
    }
  }
  if (!stillCurrent(signal)) return false

  if (manifestObj && manifestObj.artifacts.length === 0 && listedArts.length > 0) {
    manifestObj = { ...manifestObj, artifacts: listedArts }
  }
  const arts = manifestObj && manifestObj.artifacts.length > 0 ? manifestObj.artifacts : listedArts

  const scalarsArt = pickArtifact(arts, 'scalars', ['json'])
  const previewArt = pickArtifact(arts, 'preview', ['png', 'webp'])
  const meshArt = pickMeshArtifact(arts)

  const scalarsP = scalarsArt
    ? fetchOptional(() => getJobArtifact(jobId, scalarsArt.path, signal), signal)
    : Promise.resolve(null)
  const previewP = previewArt
    ? fetchOptional(() => getJobArtifactBlob(jobId, previewArt.path, signal), signal)
    : Promise.resolve(null)
  const meshP = meshArt
    ? fetchOptional(() => getJobArtifactBlob(jobId, meshArt.path, signal), signal)
    : Promise.resolve(null)
  const [scalarsRes, previewRes, meshRes] = await Promise.all([scalarsP, previewP, meshP])
  if (!stillCurrent(signal)) return false

  const scalarsBody = asScalars(scalarsRes)
  const previewBlob = previewRes instanceof Blob && previewRes.size > 0 ? previewRes : null
  const meshBlob = meshRes instanceof Blob && meshRes.size > 0 ? meshRes : null
  const gotKey = Boolean(manifestObj || scalarsBody || previewBlob || meshBlob)
  if (listedArts.length === 0 && !gotKey) {
    degradeReason.value = emptyDegradeReason(listError, manifestError)
    return false
  }

  resetViz()
  artifactBase.value = `/api/v1/jobs/${jobId}/artifacts`
  dataSource.value = 'job-artifacts'
  degradeReason.value = null
  manifest.value = manifestObj
  artifactRows.value = arts
  scalarsArtifact.value = scalarsBody

  if (!gotKey) {
    loadError.value =
      '产物列表非空，但 manifest、scalars、slice、preview 均未取到。保持 source=job-artifacts，未降级 fixture。'
  } else {
    const problems: string[] = []
    if (scalarsArt && !scalarsBody) problems.push('scalars.json')
    if (previewArt && !previewBlob) problems.push('preview')
    if (problems.length) loadError.value = `部分产物未取到：${problems.join('、')}`
  }

  if (previewBlob && previewArt) {
    const mime = previewArt.format === 'webp' ? 'image/webp' : 'image/png'
    const typed = previewBlob.type ? previewBlob : new Blob([previewBlob], { type: mime })
    const url = URL.createObjectURL(typed)
    objectUrls.push(url)
    previewUrl.value = url
  }

  if (meshBlob) {
    try {
      const buf = await meshBlob.arrayBuffer()
      if (!stillCurrent(signal)) return true
      await loadGltfBytes(buf, signal)
    } catch (e) {
      if (isAbortError(e, signal)) throw e
      if (stillCurrent(signal)) {
        gltfError.value = e instanceof Error ? e.message : String(e)
      }
    }
  } else if (meshArt) {
    gltfError.value = 'slice/surface 未取到'
  } else {
    gltfError.value = 'manifest 无 slice/surface glTF/GLB 产物'
  }
  return true
}

async function resolveJobThenLoad() {
  jobAbort?.abort()
  const controller = new AbortController()
  jobAbort = controller
  const { signal } = controller

  loading.value = true
  jobError.value = null
  degradeReason.value = null
  job.value = null
  resetViz()

  const id = queryJobId.value
  try {
    if (forceFixture.value || !id) {
      if (forceFixture.value && id) degradeReason.value = '显式 ?source=fixture'
      await loadFixtureDegraded(signal)
      return
    }

    artifactBase.value = '…'
    try {
      let j = await getJob(id, signal)
      throwIfAborted(signal)
      job.value = j
      if (!isJobTerminal(j.status)) {
        try {
          j = await pollJob(id, {
            intervalMs: 1200,
            timeoutMs: 60_000,
            signal,
            onUpdate: (u) => {
              if (stillCurrent(signal)) job.value = u
            },
          })
          if (stillCurrent(signal)) job.value = j
        } catch (e) {
          if (isAbortError(e, signal)) return
          if (e instanceof JobPollTimeoutError) {
            if (e.job && stillCurrent(signal)) job.value = e.job
            jobError.value = `轮询超时（最后状态 ${e.job?.status ?? job.value?.status ?? 'unknown'}）`
          } else {
            jobError.value = `轮询失败：${errorMessage(e)}`
          }
        }
      }
    } catch (e) {
      if (isAbortError(e, signal)) return
      if (!stillCurrent(signal)) return
      jobError.value = `读取任务失败：${errorMessage(e)}`
    }

    if (!stillCurrent(signal)) return

    const ok = await tryLoadJobArtifacts(id, signal)
    if (!stillCurrent(signal)) return
    if (ok) return

    const bits: string[] = []
    if (degradeReason.value) bits.push(degradeReason.value)
    if (job.value && job.value.status !== 'succeeded') {
      if (job.value.error?.message) jobError.value = jobError.value || job.value.error.message
      bits.push(`任务状态 ${job.value.status}`)
    } else if (!job.value && jobError.value) {
      bits.push('任务元数据不可达')
    }
    degradeReason.value = bits.join('；') || '精简产物不可达'
    await loadFixtureDegraded(signal)
  } catch (e) {
    if (isAbortError(e, signal)) return
    if (!stillCurrent(signal)) return
    jobError.value = jobError.value || `读取任务失败：${errorMessage(e)}`
    degradeReason.value = degradeReason.value || '精简产物不可达'
    try {
      await loadFixtureDegraded(signal)
    } catch (e2) {
      if (isAbortError(e2, signal)) return
      if (stillCurrent(signal)) loadError.value = errorMessage(e2)
    }
  } finally {
    if (stillCurrent(signal)) loading.value = false
  }
}

watch([queryJobId, queryResultRef, forceFixture], () => {
  void resolveJobThenLoad()
})

onMounted(() => {
  initScene()
  void resolveJobThenLoad()
})

onBeforeUnmount(() => {
  jobAbort?.abort()
  jobAbort = null
  revokeAllObjectUrls()
  teardownScene()
})
</script>

<style scoped>
.field-viz {
  display: flex;
  height: 100%;
  min-height: calc(100vh - var(--mo-header-h));
}

.field-side {
  width: 360px;
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
  overflow-wrap: anywhere;
}

.section-title {
  margin: 14px 0 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--mo-accent);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.meta-list {
  margin: 0 0 8px;
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

.mono-trunc {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.art-list {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 12px;
  font-family: var(--mo-font-mono);
}

.art-list li {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--mo-border-subtle);
}

.art-role {
  color: var(--mo-amber);
  min-width: 56px;
}

.art-fmt {
  color: var(--mo-accent);
  min-width: 36px;
}

.art-path {
  color: var(--mo-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-block {
  margin-top: 8px;
}

.preview-img {
  display: block;
  width: 64px;
  height: 64px;
  image-rendering: pixelated;
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius-sm);
  background: #111;
}

.hint {
  margin: 16px 0 0;
  font-size: 11px;
  color: var(--mo-text-muted);
  line-height: 1.4;
}

.post-panel {
  margin: 0 0 12px;
  padding: 10px 12px;
  border-radius: var(--mo-radius);
  border: 1px solid rgba(45, 212, 191, 0.4);
  background: rgba(45, 212, 191, 0.06);
}

.post-panel[data-postprocess-kind='heat-proxy'],
.post-panel[data-postprocess-kind='other'] {
  border-color: rgba(245, 158, 11, 0.45);
  background: rgba(245, 158, 11, 0.08);
}

.post-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.post-title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
}

.post-status,
.post-note {
  margin: 0 0 8px;
  font-size: 11px;
  line-height: 1.45;
}

.post-status {
  font-family: var(--mo-font-mono);
  color: var(--mo-text-secondary);
  overflow-wrap: anywhere;
}

.post-note {
  color: var(--mo-text-secondary);
}

.post-list {
  margin-bottom: 0;
}

.post-list .meta-row dd {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  text-align: right;
}

.scalar-unit {
  color: var(--mo-text-muted);
}

.cal-badge {
  font-family: var(--mo-font-mono);
  font-size: 10px;
  line-height: 1.4;
  padding: 1px 6px;
  border-radius: 999px;
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.18);
  border: 1px solid rgba(245, 158, 11, 0.45);
  white-space: nowrap;
}

.cal-badge-inline {
  font-size: 9px;
  padding: 0 5px;
}

.job-meta {
  margin-bottom: 10px;
  border-color: rgba(245, 158, 11, 0.35);
}

.degrade-note {
  margin: 0 0 10px;
  padding: 8px 10px;
  font-size: 11px;
  line-height: 1.4;
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: var(--mo-radius);
}

.live-note {
  margin: 0 0 10px;
  padding: 8px 10px;
  font-size: 11px;
  line-height: 1.4;
  color: #86efac;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.35);
  border-radius: var(--mo-radius);
}

.status-pill {
  font-family: var(--mo-font-mono);
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--mo-accent-dim);
  color: var(--mo-accent);
  text-transform: uppercase;
}

.status-pill[data-status='succeeded'] {
  background: rgba(34, 197, 94, 0.15);
  color: #86efac;
}

.status-pill[data-status='failed'],
.status-pill[data-status='cancelled'] {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}

.status-pill[data-status='queued'],
.status-pill[data-status='running'] {
  background: rgba(245, 158, 11, 0.18);
  color: #fbbf24;
}

.field-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  position: relative;
  display: flex;
  flex-direction: column;
}

.gltf-host {
  flex: 1;
  min-height: 320px;
  background: var(--mo-bg-base);
}

.gltf-host :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

.empty-hint {
  position: absolute;
  left: 0;
  right: 0;
  top: 12px;
  text-align: center;
  color: var(--mo-text-secondary);
  font-size: 13px;
  pointer-events: none;
}

.error-box {
  margin: 8px 12px;
  padding: 10px 12px;
  border-radius: var(--mo-radius);
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.35);
  color: #fca5a5;
  font-family: var(--mo-font-mono);
  font-size: 12px;
  white-space: pre-wrap;
}

@media (max-width: 960px) {
  .field-viz {
    flex-direction: column;
  }
  .field-side {
    width: 100%;
    max-height: 42vh;
    border-right: none;
    border-bottom: 1px solid var(--mo-border);
  }
}
</style>
