import { defineStore } from 'pinia'
import { computed, ref, toRaw } from 'vue'
import { getProject, getMems, getMemsFile } from '@/api/projects'
import type { MachineType, Topology } from '@/api/types'
import { readMemsMemberText } from '@/lib/memsPackageVersion'
import { composeSolveRequest } from '@/lib/composeSolveRequest'
import {
  defaultExcitation,
  defaultGeometryParams,
  defaultMaterials,
  isGeometryParams,
  machineKey,
  normalizeMachine,
  type GeometryParams,
  type UemExcitationState,
  type UemMaterialRegions,
  type UemMaterialsState,
} from '@/lib/geometryDefaults'
import {
  isUsableMeshDescriptor,
  meshFingerprint,
  REBUILD_DEBOUNCE_MS,
  requestGeometryRebuild,
  type GeometrySummarySlice,
} from '@/lib/geometryRebuild'
import { cloneJson, getPath, setPath } from '@/lib/paramPath'
import { resolveMaterials } from '@/lib/resolveMaterials'
import { getAxialSolveBackend, solveAxial } from '@/lib/axialSolve'
import { solveRadial } from '@/lib/analyticSolve'
import { useHistoryStore } from '@/stores/history'
import type { MeshDescriptor } from '@/types/mesh'
import type { Materials, OperatingPoint, SolveBackend, SolveRequest, SolveResult } from '@/types/solver'

/**
 * UEM B1：mems 子集投影 + 派生字段。无独立 uemSchemaVersion。
 * 权威仍是 mems + OpenAPI；本 store 可丢可重建。
 * 视口只订阅 meshDescriptor。求解只读当前快照，不另养一套几何。
 */

export type SessionDataSource = 'live' | 'fixture' | 'degraded'

export interface ProjectMetaState {
  projectId: string
  name: string
  topology: Topology
  machineType: MachineType
}

export interface AnalyticSlice {
  request: SolveRequest
  result: SolveResult
  source: SolveBackend | null
  solvedAt: string
}

export interface ResultsRefsState {
  /** FEM / 场图作业指针。解析 sync 不伪造 job id。 */
  lastJobId: string
  resultRef: string
  analyticSource: SolveBackend | null
}

export interface HydrateInput {
  projectId?: string
  source?: string
  topology?: string
  machineType?: string
  jobId?: string
}

const FIXTURE_MESH: Record<string, string> = {
  'RF:PMSM': '/mesh/radial_pmsm_mesh.json',
  'RF:BLDC': '/mesh/radial_pmsm_mesh.json',
  'RF:ACIM': '/mesh/radial_acim_mesh.json',
  'AF:PMSM': '/mesh/axial_af_pmsm_rfmr_mesh.json',
}

function asTopology(value: string | undefined, fallback: Topology): Topology {
  return value === 'AF' || value === 'RF' ? value : fallback
}

function asMachine(value: string | undefined, fallback: MachineType): MachineType {
  return value === 'PMSM' || value === 'BLDC' || value === 'ACIM' ? value : fallback
}

function toSolveMaterials(state: UemMaterialsState): Materials {
  const out: Materials = {}
  if (state.regions.steel) out.steel_id = state.regions.steel
  if (state.regions.magnet) out.magnet_id = state.regions.magnet
  if (state.regions.conductor) out.conductor_id = state.regions.conductor
  if (state.regions.bar) out.bar_id = state.regions.bar
  if (typeof state.inline.br_t === 'number') out.br_t = state.inline.br_t
  if (typeof state.inline.mur_pm === 'number') out.mur_pm = state.inline.mur_pm
  if (typeof state.inline.sigma_copper === 'number') out.sigma_copper = state.inline.sigma_copper
  if (typeof state.inline.sigma_bar === 'number') out.sigma_bar = state.inline.sigma_bar
  return out
}

export const useProjectSession = defineStore('projectSession', () => {
  const history = useHistoryStore()

  const phase = ref<'loading' | 'ready'>('loading')
  const projectMeta = ref<ProjectMetaState>({
    projectId: '',
    name: '',
    topology: 'RF',
    machineType: 'PMSM',
  })
  const geometryParams = ref<GeometryParams>(defaultGeometryParams('RF', 'PMSM'))
  const materials = ref<UemMaterialsState>(defaultMaterials('PMSM'))
  const excitation = ref<UemExcitationState>(defaultExcitation('RF', 'PMSM'))
  const meshDescriptor = ref<MeshDescriptor | null>(null)
  const geometrySummary = ref<GeometrySummarySlice | null>(null)
  const pipelineEntry = ref<Record<string, unknown> | null>(null)
  const paramsHash = ref<string>('')
  const geometryDirty = ref(false)
  const dataSource = ref<SessionDataSource>('fixture')
  const fixtureReason = ref('')
  const rebuilding = ref(false)
  const rebuildError = ref('')
  const viewportRev = ref(0)
  const solving = ref(false)
  const solveError = ref('')
  const analyticStale = ref(false)
  const analytic = ref<AnalyticSlice | null>(null)
  const resultsRefs = ref<ResultsRefsState>({
    lastJobId: '',
    resultRef: '',
    analyticSource: null,
  })

  let rebuildSeq = 0
  let hydrateEpoch = 0
  let rebuildTimer: ReturnType<typeof setTimeout> | null = null
  let applyingHistory = false

  const machineLabel = computed(() => machineKey(projectMeta.value.topology, projectMeta.value.machineType))
  const canUndo = computed(() => history.canUndo)
  const canRedo = computed(() => history.canRedo)
  const historyCursor = computed(() => history.cursor)
  const historyLength = computed(() => history.entries.length)

  function cancelRebuildTimer() {
    if (rebuildTimer) {
      clearTimeout(rebuildTimer)
      rebuildTimer = null
    }
  }

  function markAnalyticStale() {
    if (analytic.value) analyticStale.value = true
  }

  function applyMachineTemplates(topology: Topology, machineType: MachineType) {
    materials.value = defaultMaterials(machineType)
    excitation.value = defaultExcitation(topology, machineType)
  }

  function syncMetaFromParams(params: GeometryParams) {
    const topology = asTopology(params.topology, projectMeta.value.topology)
    const machineType = asMachine(params.machineType, projectMeta.value.machineType)
    const normalized = normalizeMachine(topology, machineType)
    projectMeta.value = {
      ...projectMeta.value,
      topology: normalized.topology,
      machineType: normalized.machineType,
    }
  }

  async function loadParamsFromProject(projectId: string): Promise<GeometryParams | null> {
    try {
      const blob = await getMemsFile(projectId, 'geometry/params.json')
      const text = await blob.text()
      const parsed: unknown = JSON.parse(text)
      if (isGeometryParams(parsed)) return parsed
    } catch {
      /* 成员读失败再走整包 */
    }
    try {
      const zip = await getMems(projectId)
      const text = await readMemsMemberText(new Uint8Array(await zip.arrayBuffer()), 'geometry/params.json')
      if (!text) return null
      const parsed: unknown = JSON.parse(text)
      return isGeometryParams(parsed) ? parsed : null
    } catch {
      return null
    }
  }

  async function applyFixtureMesh(
    reason: string,
    guard: () => boolean,
    source: SessionDataSource = 'fixture',
  ) {
    const key = machineKey(projectMeta.value.topology, projectMeta.value.machineType)
    const url = FIXTURE_MESH[key] ?? FIXTURE_MESH['RF:PMSM']
    let detail = reason
    if (key === 'RF:BLDC') {
      detail = `${reason}；RF-BLDC 无独立 public/mesh，降级显示 RF-PMSM 样例网格`
    }
    try {
      const res = await fetch(url)
      if (!guard()) return
      if (!res.ok) throw new Error(`fixture ${res.status}`)
      const data: unknown = await res.json()
      if (!guard()) return
      if (!isUsableMeshDescriptor(data)) throw new Error('fixture 描述符不可用')
      const nextKey = meshFingerprint(data)
      const prevKey = meshFingerprint(meshDescriptor.value)
      meshDescriptor.value = data
      if (nextKey !== prevKey) viewportRev.value += 1
    } catch (err) {
      if (!guard()) return
      meshDescriptor.value = null
      viewportRev.value += 1
      detail = `${detail}；样例网格读取失败：${err instanceof Error ? err.message : String(err)}`
    }
    if (!guard()) return
    geometrySummary.value = null
    pipelineEntry.value = null
    paramsHash.value = ''
    dataSource.value = source
    fixtureReason.value = detail
  }

  async function rebuildNow() {
    cancelRebuildTimer()
    const seq = ++rebuildSeq
    rebuilding.value = true
    rebuildError.value = ''
    const topology = projectMeta.value.topology
    const machineType = projectMeta.value.machineType
    const params = cloneJson(toRaw(geometryParams.value))
    try {
      const outcome = await requestGeometryRebuild({
        topology,
        machineType,
        params,
      })
      if (seq !== rebuildSeq) return
      if (JSON.stringify(params) !== JSON.stringify(toRaw(geometryParams.value))) return
      if (!outcome.ok) {
        rebuildError.value = outcome.message
        await applyFixtureMesh(
          outcome.message || 'geometry/rebuild 失败',
          () => seq === rebuildSeq,
          'degraded',
        )
        return
      }
      const live = outcome.live
      const nextPrint = meshFingerprint(live.meshDescriptor)
      const prevPrint = meshFingerprint(meshDescriptor.value)
      const meshChanged = nextPrint !== prevPrint
      const summaryChanged =
        JSON.stringify(geometrySummary.value) !== JSON.stringify(live.geometrySummary)
      meshDescriptor.value = live.meshDescriptor
      geometrySummary.value = live.geometrySummary
      pipelineEntry.value = live.pipelineEntry ?? null
      paramsHash.value = live.paramsHash ?? ''
      dataSource.value = 'live'
      fixtureReason.value = ''
      geometryDirty.value = false
      rebuildError.value = ''
      if (meshChanged) viewportRev.value += 1
      if (meshChanged || summaryChanged) markAnalyticStale()
    } finally {
      if (seq === rebuildSeq) rebuilding.value = false
    }
  }

  function scheduleRebuild() {
    cancelRebuildTimer()
    rebuildTimer = setTimeout(() => {
      rebuildTimer = null
      void rebuildNow()
    }, REBUILD_DEBOUNCE_MS)
  }

  function commitParam(path: string, value: unknown) {
    if (phase.value !== 'ready') return
    if (value === undefined) return
    const before = getPath(geometryParams.value, path)
    if (Object.is(before, value)) return
    const next = cloneJson(toRaw(geometryParams.value))
    setPath(next, path, value)
    if (!applyingHistory) {
      history.push({
        commandType: 'geometry.params.set',
        summary: `设置 ${path} = ${String(value)}`,
        payload: { path, before, after: value },
        inverse: { path, before: value, after: before },
      })
    }
    geometryParams.value = next
    geometryDirty.value = true
    markAnalyticStale()
    scheduleRebuild()
  }

  function applyHistoryEntry(
    entry: { commandType: string; payload?: Record<string, unknown>; inverse?: Record<string, unknown> },
    direction: 'undo' | 'redo',
  ) {
    if (entry.commandType !== 'geometry.params.set') return
    const patch =
      direction === 'undo'
        ? (entry.inverse ??
          (entry.payload
            ? { path: entry.payload.path, before: entry.payload.after, after: entry.payload.before }
            : undefined))
        : entry.payload
    if (!patch || typeof patch.path !== 'string') return
    applyingHistory = true
    try {
      commitParam(patch.path, patch.after)
    } finally {
      applyingHistory = false
    }
  }

  function undo() {
    if (phase.value !== 'ready') return
    const entry = history.undo()
    if (!entry) return
    applyHistoryEntry(entry, 'undo')
  }

  function redo() {
    if (phase.value !== 'ready') return
    const entry = history.redo()
    if (!entry) return
    applyHistoryEntry(entry, 'redo')
  }

  function setMachine(topology: Topology, machineType: MachineType) {
    const normalized = normalizeMachine(topology, machineType)
    if (
      normalized.topology === projectMeta.value.topology &&
      normalized.machineType === projectMeta.value.machineType
    ) {
      return
    }
    history.clear()
    projectMeta.value = { ...projectMeta.value, ...normalized }
    geometryParams.value = defaultGeometryParams(normalized.topology, normalized.machineType)
    applyMachineTemplates(normalized.topology, normalized.machineType)
    analytic.value = null
    analyticStale.value = false
    solveError.value = ''
    geometryDirty.value = true
    void rebuildNow()
  }

  function commitRegion(key: keyof UemMaterialRegions, value: string) {
    materials.value = {
      ...materials.value,
      regions: { ...materials.value.regions, [key]: value },
    }
    markAnalyticStale()
  }

  function commitInline(key: keyof UemMaterialsState['inline'], value: number | undefined) {
    if (value === undefined || !Number.isFinite(value)) return
    materials.value = {
      ...materials.value,
      inline: { ...materials.value.inline, [key]: value },
    }
    markAnalyticStale()
  }

  function commitOperatingPoint(patch: Partial<OperatingPoint>) {
    excitation.value = {
      ...excitation.value,
      operatingPoint: { ...excitation.value.operatingPoint, ...patch },
    }
    markAnalyticStale()
  }

  function setDriveMode(mode: string) {
    excitation.value = {
      ...excitation.value,
      driveDraft: mode ? { mode } : undefined,
    }
  }

  function noteFemJob(jobId: string) {
    resultsRefs.value = { ...resultsRefs.value, lastJobId: jobId }
  }

  async function solveExplicit() {
    solveError.value = ''
    if (dataSource.value !== 'live' || !geometrySummary.value) {
      solveError.value = '没有 live geometrySummary。fixture 不能当作求解几何。'
      return
    }
    if (geometryDirty.value || rebuilding.value) {
      solveError.value = '几何仍在重建或未成功，请待重建完成后再求解。'
      return
    }
    if (projectMeta.value.topology === 'AF' && projectMeta.value.machineType !== 'PMSM') {
      solveError.value = 'AF 非 PMSM 不在本壳求解范围。'
      return
    }
    solving.value = true
    try {
      const inline = toSolveMaterials(materials.value)
      const resolved = await resolveMaterials(inline)
      const request = composeSolveRequest({
        topology: projectMeta.value.topology,
        machineType: projectMeta.value.machineType,
        geometry: geometrySummary.value,
        materials: resolved.inline,
        operatingPoint: { ...excitation.value.operatingPoint },
      })
      const result =
        projectMeta.value.topology === 'AF' ? await solveAxial(request) : await solveRadial(request)
      const source =
        result.meta.source ??
        (projectMeta.value.topology === 'AF' ? getAxialSolveBackend() : null)
      analytic.value = {
        request,
        result,
        source,
        solvedAt: new Date().toISOString(),
      }
      analyticStale.value = false
      resultsRefs.value = {
        ...resultsRefs.value,
        analyticSource: source,
      }
    } catch (err) {
      solveError.value = err instanceof Error ? err.message : String(err)
    } finally {
      solving.value = false
    }
  }

  async function hydrate(input: HydrateInput) {
    const epoch = ++hydrateEpoch
    rebuildSeq += 1
    cancelRebuildTimer()
    phase.value = 'loading'
    meshDescriptor.value = null
    geometrySummary.value = null
    pipelineEntry.value = null
    paramsHash.value = ''
    rebuildError.value = ''
    solveError.value = ''
    analytic.value = null
    analyticStale.value = false
    history.clear()
    const still = () => epoch === hydrateEpoch

    const hinted = normalizeMachine(
      asTopology(input.topology, 'RF'),
      asMachine(input.machineType, 'PMSM'),
    )
    projectMeta.value = {
      projectId: input.projectId ?? '',
      name: '',
      topology: hinted.topology,
      machineType: hinted.machineType,
    }
    if (input.jobId) noteFemJob(input.jobId)

    if (input.projectId) {
      try {
        const project = await getProject(input.projectId)
        if (!still()) return
        projectMeta.value = {
          ...projectMeta.value,
          projectId: project.id,
          name: project.name,
          topology: project.topology,
          machineType: project.machineType,
        }
        const normalized = normalizeMachine(project.topology, project.machineType)
        projectMeta.value = { ...projectMeta.value, ...normalized }
      } catch {
        /* 元数据失败仍尝试读 params */
      }
    }

    if (input.source === 'fixture') {
      geometryParams.value = defaultGeometryParams(projectMeta.value.topology, projectMeta.value.machineType)
      applyMachineTemplates(projectMeta.value.topology, projectMeta.value.machineType)
      geometryDirty.value = false
      await applyFixtureMesh('显式 ?source=fixture', still)
      if (!still()) return
      phase.value = 'ready'
      return
    }

    if (input.projectId) {
      const loaded = await loadParamsFromProject(input.projectId)
      if (!still()) return
      if (loaded) {
        geometryParams.value = loaded
        syncMetaFromParams(loaded)
        applyMachineTemplates(projectMeta.value.topology, projectMeta.value.machineType)
        geometryDirty.value = true
        await rebuildNow()
        if (!still()) return
        phase.value = 'ready'
        return
      }
      geometryParams.value = defaultGeometryParams(projectMeta.value.topology, projectMeta.value.machineType)
      applyMachineTemplates(projectMeta.value.topology, projectMeta.value.machineType)
      geometryDirty.value = true
      await applyFixtureMesh('无法读取 mems geometry/params.json', still)
      if (!still()) return
      phase.value = 'ready'
      return
    }

    geometryParams.value = defaultGeometryParams(projectMeta.value.topology, projectMeta.value.machineType)
    applyMachineTemplates(projectMeta.value.topology, projectMeta.value.machineType)
    geometryDirty.value = true
    await rebuildNow()
    if (!still()) return
    phase.value = 'ready'
  }

  return {
    phase,
    projectMeta,
    geometryParams,
    materials,
    excitation,
    meshDescriptor,
    geometrySummary,
    pipelineEntry,
    paramsHash,
    geometryDirty,
    dataSource,
    fixtureReason,
    rebuilding,
    rebuildError,
    viewportRev,
    solving,
    solveError,
    analyticStale,
    analytic,
    resultsRefs,
    machineLabel,
    canUndo,
    canRedo,
    historyCursor,
    historyLength,
    hydrate,
    commitParam,
    undo,
    redo,
    setMachine,
    commitRegion,
    commitInline,
    commitOperatingPoint,
    setDriveMode,
    noteFemJob,
    solveExplicit,
  }
})
