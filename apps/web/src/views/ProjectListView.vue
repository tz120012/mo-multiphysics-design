<template>
  <div class="project-page">
    <div class="project-toolbar">
      <div>
        <h2 class="page-title">工程列表</h2>
        <p class="page-desc">
          本地假数据 · 未接后端 · memsSchemaVersion={{ memsVersion }}
        </p>
      </div>
      <el-button type="primary" @click="dialogVisible = true">新建工程</el-button>
    </div>

    <div class="project-table-wrap">
      <el-table :data="projects.items" stripe empty-text="暂无工程" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="220" />
        <el-table-column label="机型" width="100">
          <template #default="{ row }">
            {{ MACHINE_TYPE_LABELS[row.machineType as MachineType] }}
          </template>
        </el-table-column>
        <el-table-column label="拓扑" width="120">
          <template #default="{ row }">
            {{ TOPOLOGY_LABELS[row.topology as Topology] }}
            <span class="enum-code">({{ row.topology }})</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span class="status-pill" :data-status="row.uiStatus || 'draft'">
              {{ statusLabel(row.uiStatus) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updatedAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default>
            <el-button text type="primary" disabled title="Q1-4/5 工作区占位">打开</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      title="新建工程"
      width="420px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：无人机推进 PMSM" />
        </el-form-item>
        <el-form-item label="机型" prop="machineType">
          <el-select v-model="form.machineType" placeholder="选择机型" style="width: 100%">
            <el-option
              v-for="(label, value) in MACHINE_TYPE_LABELS"
              :key="value"
              :label="label"
              :value="value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="拓扑" prop="topology">
          <el-select v-model="form.topology" placeholder="选择拓扑" style="width: 100%">
            <el-option
              v-for="(label, value) in TOPOLOGY_LABELS"
              :key="value"
              :label="`${label} (${value})`"
              :value="value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import {
  MACHINE_TYPE_LABELS,
  MEMS_SCHEMA_VERSION,
  TOPOLOGY_LABELS,
  type MachineType,
  type Topology,
} from '@/api/types'
import { useProjectsStore } from '@/stores/projects'

const projects = useProjectsStore()
const memsVersion = MEMS_SCHEMA_VERSION
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  machineType: 'PMSM' as MachineType,
  topology: 'RF' as Topology,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入工程名称', trigger: 'blur' }],
  machineType: [{ required: true, message: '请选择机型', trigger: 'change' }],
  topology: [{ required: true, message: '请选择拓扑', trigger: 'change' }],
}

function statusLabel(s?: string) {
  const map: Record<string, string> = { draft: '草稿', ready: '就绪', running: '计算中' }
  return map[s || 'draft'] || '草稿'
}

function formatTime(iso: string) {
  try {
    const d = new Date(iso)
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return iso
  }
}

function resetForm() {
  form.name = ''
  form.machineType = 'PMSM'
  form.topology = 'RF'
}

async function onCreate() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  projects.addProject({
    name: form.name,
    machineType: form.machineType,
    topology: form.topology,
  })
  dialogVisible.value = false
  ElMessage.success('已创建（本地占位，未调 API）')
}
</script>

<style scoped>
.project-page {
  padding: 16px 20px 24px;
  max-width: 1100px;
}

.project-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 14px;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.page-desc {
  margin: 4px 0 0;
  color: var(--mo-text-muted);
  font-size: 12px;
  font-family: var(--mo-font-mono);
}

.project-table-wrap {
  background: var(--mo-bg-panel);
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius);
  overflow: hidden;
}

.enum-code {
  color: var(--mo-text-muted);
  font-family: var(--mo-font-mono);
  font-size: 11px;
  margin-left: 2px;
}

.status-pill {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid var(--mo-border);
  color: var(--mo-text-secondary);
}

.status-pill[data-status='ready'] {
  border-color: rgba(45, 212, 191, 0.45);
  color: var(--mo-accent);
  background: var(--mo-accent-dim);
}

.status-pill[data-status='running'] {
  border-color: rgba(245, 158, 11, 0.45);
  color: var(--mo-amber);
  background: var(--mo-amber-dim);
}

:deep(.el-table) {
  --el-table-bg-color: var(--mo-bg-panel);
  --el-table-tr-bg-color: var(--mo-bg-panel);
  --el-table-header-bg-color: var(--mo-bg-elevated);
  --el-table-row-hover-bg-color: var(--mo-bg-hover);
  --el-table-border-color: var(--mo-border-subtle);
  font-size: 13px;
}
</style>
