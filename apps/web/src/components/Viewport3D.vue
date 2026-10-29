<template>
  <div ref="hostRef" class="viewport3d" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import type { MeshDescriptor } from '@/types/mesh'
import { disposeObject3D, meshDescriptorToGroup } from '@/lib/meshToThree'

const props = defineProps<{
  descriptor: MeshDescriptor | null
}>()

const hostRef = ref<HTMLDivElement | null>(null)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let meshRoot: THREE.Group | null = null
let animId = 0
let resizeObserver: ResizeObserver | null = null

function clearMeshRoot() {
  if (!scene || !meshRoot) return
  scene.remove(meshRoot)
  disposeObject3D(meshRoot)
  meshRoot = null
}

function fitCameraToObject(object: THREE.Object3D) {
  if (!camera || !controls) return
  const box = new THREE.Box3().setFromObject(object)
  if (box.isEmpty()) return
  const size = box.getSize(new THREE.Vector3())
  const center = box.getCenter(new THREE.Vector3())
  const maxDim = Math.max(size.x, size.y, size.z, 1e-4)
  const dist = maxDim * 2.2
  camera.near = Math.max(dist / 200, 1e-4)
  camera.far = dist * 50
  camera.position.set(center.x + dist * 0.7, center.y + dist * 0.55, center.z + dist * 0.9)
  camera.lookAt(center)
  camera.updateProjectionMatrix()
  controls.target.copy(center)
  controls.update()
}

function applyDescriptor(descriptor: MeshDescriptor | null) {
  if (!scene) return
  clearMeshRoot()
  if (!descriptor) return
  meshRoot = meshDescriptorToGroup(descriptor)
  scene.add(meshRoot)
  fitCameraToObject(meshRoot)
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
  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

function init() {
  const host = hostRef.value
  if (!host) return

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0e0f11)

  const w = host.clientWidth || 1
  const h = host.clientHeight || 1
  camera = new THREE.PerspectiveCamera(45, w / h, 0.001, 100)
  camera.position.set(0.08, 0.06, 0.1)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
  renderer.setSize(w, h, false)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  host.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08

  const ambient = new THREE.AmbientLight(0xffffff, 0.55)
  scene.add(ambient)
  const key = new THREE.DirectionalLight(0xffffff, 0.85)
  key.position.set(2, 3, 4)
  scene.add(key)
  const fill = new THREE.DirectionalLight(0xa5b4fc, 0.35)
  fill.position.set(-2, -1, -2)
  scene.add(fill)

  const axes = new THREE.AxesHelper(0.05)
  axes.name = 'axes'
  scene.add(axes)

  const grid = new THREE.GridHelper(0.2, 20, 0x2a2d34, 0x1f2228)
  grid.rotation.x = Math.PI / 2
  grid.name = 'grid'
  scene.add(grid)

  resizeObserver = new ResizeObserver(() => handleResize())
  resizeObserver.observe(host)
  window.addEventListener('resize', handleResize)

  applyDescriptor(props.descriptor)
  animate()
}

function teardown() {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
  resizeObserver = null
  clearMeshRoot()
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

onMounted(() => init())
onBeforeUnmount(() => teardown())

watch(
  () => props.descriptor,
  (next) => applyDescriptor(next),
  { deep: true },
)
</script>

<style scoped>
.viewport3d {
  width: 100%;
  height: 100%;
  min-height: 320px;
  background: var(--mo-bg-base);
  overflow: hidden;
}

.viewport3d :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
</style>
