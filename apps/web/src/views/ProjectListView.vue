<template>
  <div class="project-page">
    <div class="project-toolbar">
      <div>
        <h2 class="page-title">工程列表</h2>
        <p class="page-desc">本地假数据 · 未接后端 API</p>
      </div>
      <el-button type="primary" @click="dialogVisible = true">新建工程</el-button>
    </div>

    <div class="project-table-wrap">
      <el-table :data="projects.items" stripe empty-text="暂无工程" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="220" />
        <el-table-column prop="machineType" label="机型" width="100" />
        <el-table-column prop="topology" label="拓扑" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <span class="status-pill" :data-status="row.status">{{ statusLabel(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="160" />
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
            <el-option label="PMSM" value="PMSM" />
            <el-option label="BLDC" value="BLDC" />
            <el-option label="ACIM" value="ACIM" />
          </el-select>
        </el-form-item>
        <el-form-item label="拓扑" prop="topology">
          <el-select v-model="form.topology" placeholder="选择拓扑" style="width: 100%">
            <el-option label="径向磁通" value="径向磁通" />
            <el-option label="轴向磁通" value="轴向磁通" />
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
import { useProjectsStore, type ProjectItem } from '@/stores/projects'

const projects = useProjectsStore()
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  machineType: 'PMSM',
  topology: '径向磁通',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入工程名称', trigger: 'blur' }],
  machineType: [{ required: true, message: '请选择机型', trigger: 'change' }],
  topology: [{ required: true, message: '请选择拓扑', trigger: 'change' }],
}

function statusLabel(s: ProjectItem['status']) {
  const map = { draft: '草稿', ready: '就绪', running: '计算中' } as const
  return map[s]
}

function resetForm() {
  form.name = ''
  form.machineType = 'PMSM'
  form.topology = '径向磁通'
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
}

.project-table-wrap {
  background: var(--mo-bg-panel);
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius);
  overflow: hidden;
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
