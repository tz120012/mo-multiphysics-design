<template>
  <div class="field-viz">
    <aside class="field-side">
      <h2 class="side-title">场量 · 精简可视化</h2>
      <p class="side-desc">
        Q3-6 · manifest §5 · {{ FEM_MANIFEST_FIXTURE_BASE }}
      </p>

      <div v-if="loadError" class="error-box">{{ loadError }}</div>

      <template v-if="manifest">
        <dl class="meta-list">
          <div class="meta-row"><dt>jobId</dt><dd class="mono-trunc" :title="manifest.jobId">{{ shortId(manifest.jobId) }}</dd></div>
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

        <h3 class="section-title">artifacts</h3>
        <ul class="art-list">
          <li v-for="(a, i) in manifest.artifacts" :key="i">
            <span class="art-role">{{ a.role }}</span>
            <span class="art-fmt">{{ a.format }}</span>
            <span class="art-path" :title="a.path">{{ basename(a.path) }}</span>
          </li>
        </ul>

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
      </template>

      <p class="hint">
        仅消费精简 JSON / glTF / PNG（docs/drafts/Q3-轴向与FEM边界.md §5）。禁止默认 VTK/全场。
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import {
  FEM_MANIFEST_FIXTURE_BASE,
  type FemArtifact,
  type FemManifest,
  type FemScalarsArtifact,
} from '@/types/fieldViz'
import { disposeObject3D } from '@/lib/meshToThree'

const manifest = ref<FemManifest | null>(null)
const scalarsArtifact = ref<FemScalarsArtifact | null>(null)
const loadError = ref<string | null>(null)
const gltfError = ref<string | null>(null)
const meshLoaded = ref(false)
const previewUrl = ref<string | null>(null)
const hostRef = ref<HTMLDivElement | null>(null)

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

/** manifest 内 path 可能是 .mems 相对路径；本 tip mock 文件落在 fixture 目录根，用 basename 解析 */
function resolveArtifactUrl(artifact: FemArtifact): string {
  return `${FEM_MANIFEST_FIXTURE_BASE}/${basename(artifact.path)}`
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

async function loadGltf(url: string) {
  if (!scene) return
  clearMesh()
  gltfError.value = null
  meshLoaded.value = false
  const loader = new GLTFLoader()
  try {
    const gltf = await loader.loadAsync(url)
    meshRoot = gltf.scene
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
  } catch (e) {
    gltfError.value = e instanceof Error ? e.message : String(e)
  }
}

async function loadFixture() {
  loadError.value = null
  try {
    const res = await fetch(`${FEM_MANIFEST_FIXTURE_BASE}/manifest.json`)
    if (!res.ok) throw new Error(`manifest ${res.status}`)
    const m = (await res.json()) as FemManifest
    manifest.value = m

    const scalarsArt = m.artifacts.find((a) => a.role === 'scalars' && a.format === 'json')
    if (scalarsArt) {
      const sRes = await fetch(resolveArtifactUrl(scalarsArt))
      if (sRes.ok) scalarsArtifact.value = (await sRes.json()) as FemScalarsArtifact
    }

    const previewArt = m.artifacts.find((a) => a.role === 'preview' && (a.format === 'png' || a.format === 'webp'))
    previewUrl.value = previewArt ? resolveArtifactUrl(previewArt) : null

    const meshArt =
      m.artifacts.find((a) => (a.role === 'slice' || a.role === 'surface') && (a.format === 'glb' || a.format === 'gltf')) ??
      null
    if (meshArt) {
      await loadGltf(resolveArtifactUrl(meshArt))
    } else {
      gltfError.value = 'manifest 无 slice/surface glTF/GLB 产物'
    }
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : String(e)
  }
}

onMounted(() => {
  initScene()
  void loadFixture()
})

onBeforeUnmount(() => teardownScene())
</script>

<style scoped>
.field-viz {
  display: flex;
  height: 100%;
  min-height: calc(100vh - var(--mo-header-h));
}

.field-side {
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
