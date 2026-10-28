import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as projectsApi from '@/api/projects'
import type { MachineType, Project, ProjectCreate, Topology } from '@/api/types'

/** 列表 UI 本地装饰字段（勿写入 API body） */
export type ProjectListItem = Project & {
  uiStatus?: 'draft' | 'ready' | 'running'
}

export const useProjectsStore = defineStore('projects', () => {
  const items = ref<ProjectListItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchProjects() {
    loading.value = true
    error.value = null
    try {
      const res = await projectsApi.listProjects()
      items.value = res.items.map((p) => ({ ...p, uiStatus: 'draft' as const }))
      total.value = res.total
    } catch (e) {
      items.value = []
      total.value = 0
      error.value = e instanceof Error ? e.message : String(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function addProject(payload: ProjectCreate) {
    const created = await projectsApi.createProject(payload)
    items.value.unshift({ ...created, uiStatus: 'draft' })
    total.value += 1
    return created
  }

  return { items, total, loading, error, fetchProjects, addProject }
})

export type { Topology, MachineType, ProjectCreate }
