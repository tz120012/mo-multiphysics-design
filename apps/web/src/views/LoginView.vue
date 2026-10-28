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
        <el-form-item label="账号" prop="account">
          <el-input
            v-model="form.account"
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
      <p class="login-hint">Q1 占位：提交后假登录，token 写入 localStorage</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  account: 'engineer',
  password: 'demo',
})

const rules: FormRules = {
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    auth.login(form.account, form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/projects'
    await router.replace(redirect)
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
  background:
    radial-gradient(ellipse at 30% 20%, rgba(45, 212, 191, 0.06), transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(245, 158, 11, 0.04), transparent 45%),
    var(--mo-bg-base);
}

.login-panel {
  width: 360px;
  padding: 28px 28px 20px;
  background: var(--mo-bg-panel);
  border: 1px solid var(--mo-border);
  border-radius: var(--mo-radius);
}

.login-brand {
  text-align: center;
  margin-bottom: 24px;
}

.login-logo {
  display: inline-block;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--mo-accent);
  box-shadow: inset 0 0 0 5px var(--mo-bg-panel), inset 0 0 0 8px var(--mo-amber);
  margin-bottom: 10px;
}

.login-brand h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
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
  margin: 4px 0 0;
  text-align: center;
  color: var(--mo-text-muted);
  font-size: 11px;
}

:deep(.el-form-item__label) {
  color: var(--mo-text-secondary);
}
</style>
