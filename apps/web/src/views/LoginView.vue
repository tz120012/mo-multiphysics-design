<template>
  <div class="login-page">
    <div class="login-panel">
      <div class="login-brand">
        <span class="login-logo" aria-hidden="true" />
        <h1>Mo</h1>
        <p>电机多物理场智能设计平台</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="账号" prop="username">
          <el-input
            v-model="form.username"
            placeholder="任意账号（演示）"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="任意密码（演示）"
            show-password
            autocomplete="current-password"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="onSubmit">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <p class="login-hint">POST /auth/login · body.username · token → localStorage</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  username: 'engineer',
  password: 'demo',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function errorMessage(e: unknown): string {
  if (axios.isAxiosError(e)) {
    const detail = e.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return String((detail as { message: string }).message)
    }
    return e.message
  }
  return e instanceof Error ? e.message : String(e)
}

async function onSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/projects'
    await router.replace(redirect)
  } catch (e) {
    ElMessage.error(`登录失败：${errorMessage(e)}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 24px;
  background:
    radial-gradient(ellipse at 20% 0%, rgba(45, 212, 191, 0.08), transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(245, 158, 11, 0.06), transparent 45%),
    var(--mo-bg-base);
}

.login-panel {
  width: 100%;
  max-width: 360px;
  padding: 28px 28px 22px;
  background: var(--mo-bg-panel);
  border: 1px solid var(--mo-border);
  border-radius: 8px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
}

.login-brand {
  text-align: center;
  margin-bottom: 22px;
}

.login-logo {
  display: inline-block;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--mo-accent);
  box-shadow: inset 0 0 0 4px var(--mo-bg-panel), inset 0 0 0 7px var(--mo-amber);
  margin-bottom: 10px;
}

.login-brand h1 {
  margin: 0;
  font-size: 22px;
  letter-spacing: 0.06em;
}

.login-brand p {
  margin: 6px 0 0;
  color: var(--mo-text-muted);
  font-size: 12px;
}

.login-btn {
  width: 100%;
}

.login-hint {
  margin: 8px 0 0;
  text-align: center;
  color: var(--mo-text-muted);
  font-size: 11px;
  font-family: var(--mo-font-mono);
}
</style>
