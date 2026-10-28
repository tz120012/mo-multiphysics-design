import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ProjectItem {
  id: string
  name: string
  topology: string
  machineType: string
  updatedAt: string
  status: 'draft' | 'ready' | 'running'
}

/** 示例假数据 — Q1 不调真实 API */
const SEED: ProjectItem[] = [
  {
    id: 'prj-001',
    name: 'eVTOL 主推进 PMSM-120kW',
    topology: '径向磁通',
    machineType: 'PMSM',
    updatedAt: '2026-10-26 14:22',
    status: 'ready',
  },
  {
    id: 'prj-002',
    name: '多旋翼 BLDC-5kW 演示',
    topology: '径向磁通',
    machineType: 'BLDC',
    updatedAt: '2026-10-25 09:10',
    status: 'draft',
  },
  {
    id: 'prj-003',
    name: '轴向涵道 ACIM-80kW',
    topology: '径向磁通',
    machineType: 'ACIM',
    updatedAt: '2026-10-24 18:45',
    status: 'running',
  },
]

export const useProjectsStore = defineStore('projects', () => {
  const items = ref<ProjectItem[]>([...SEED])

  function addProject(payload: Pick<ProjectItem, 'name' | 'topology' | 'machineType'>) {
    const now = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`
    items.value.unshift({
      id: `prj-${Date.now()}`,
      name: payload.name,
      topology: payload.topology,
      machineType: payload.machineType,
      updatedAt: stamp,
      status: 'draft',
    })
  }

  return { items, addProject }
})
