import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  MEMS_SCHEMA_VERSION,
  type MachineType,
  type Project,
  type ProjectCreate,
  type Topology,
} from '@/api/types'

/** 列表 UI 本地装饰字段（非 OpenAPI Project） */
export type ProjectListItem = Project & {
  /** 本地假状态，后端契约暂无此字段 */
  uiStatus?: 'draft' | 'ready' | 'running'
}

const SEED: ProjectListItem[] = [
  {
    id: '11111111-1111-4111-8111-111111111101',
    name: 'eVTOL 主推进 PMSM-120kW',
    topology: 'RF',
    machineType: 'PMSM',
    memsSchemaVersion: MEMS_SCHEMA_VERSION,
    createdAt: '2026-10-24T10:00:00+08:00',
    updatedAt: '2026-10-26T14:22:00+08:00',
    uiStatus: 'ready',
  },
  {
    id: '11111111-1111-4111-8111-111111111102',
    name: '多旋翼 BLDC-5kW 演示',
    topology: 'RF',
    machineType: 'BLDC',
    memsSchemaVersion: MEMS_SCHEMA_VERSION,
    createdAt: '2026-10-23T09:00:00+08:00',
    updatedAt: '2026-10-25T09:10:00+08:00',
    uiStatus: 'draft',
  },
  {
    id: '11111111-1111-4111-8111-111111111103',
    name: '轴向涵道 ACIM-80kW',
    topology: 'AF',
    machineType: 'ACIM',
    memsSchemaVersion: MEMS_SCHEMA_VERSION,
    createdAt: '2026-10-22T18:00:00+08:00',
    updatedAt: '2026-10-24T18:45:00+08:00',
    uiStatus: 'running',
  },
]

export const useProjectsStore = defineStore('projects', () => {
  const items = ref<ProjectListItem[]>([...SEED])

  function addProject(payload: ProjectCreate) {
    const now = new Date().toISOString()
    items.value.unshift({
      id: crypto.randomUUID(),
      name: payload.name,
      topology: payload.topology,
      machineType: payload.machineType,
      memsSchemaVersion: MEMS_SCHEMA_VERSION,
      createdAt: now,
      updatedAt: now,
      uiStatus: 'draft',
    })
  }

  return { items, addProject }
})

export type { Topology, MachineType, ProjectCreate }
