<template>
  <div class="mo-shell">
    <header class="mo-header">
      <div class="mo-brand">
        <span class="mo-logo" aria-hidden="true" />
        <span class="mo-title">Mo</span>
        <span class="mo-subtitle">电机设计平台</span>
      </div>
      <nav class="mo-nav">
        <router-link to="/projects" class="mo-nav-link" active-class="is-active">
          工程
        </router-link>
        <router-link to="/workspace" class="mo-nav-link" active-class="is-active">
          工作区
        </router-link>
      </nav>
      <div class="mo-header-right">
        <span class="mo-user">{{ auth.username }}</span>
        <el-button text type="info" @click="onLogout">退出</el-button>
      </div>
    </header>
    <main class="mo-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function onLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.mo-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--mo-bg-base);
}

.mo-header {
  display: flex;
  align-items: center;
  gap: 24px;
  height: var(--mo-header-h);
  padding: 0 16px;
  background: var(--mo-bg-panel);
  border-bottom: 1px solid var(--mo-border);
  flex-shrink: 0;
}

.mo-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mo-logo {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--mo-accent);
  box-shadow: inset 0 0 0 3px var(--mo-bg-panel), inset 0 0 0 5px var(--mo-amber);
}

.mo-title {
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.04em;
  color: var(--mo-text-primary);
}

.mo-subtitle {
  font-size: 12px;
  color: var(--mo-text-muted);
  border-left: 1px solid var(--mo-border);
  padding-left: 8px;
}

.mo-nav {
  display: flex;
  gap: 4px;
  flex: 1;
}

.mo-nav-link {
  padding: 4px 10px;
  border-radius: var(--mo-radius-sm);
  color: var(--mo-text-secondary);
  text-decoration: none;
  font-size: 13px;
}

.mo-nav-link:hover {
  color: var(--mo-text-primary);
  background: var(--mo-bg-hover);
  text-decoration: none;
}

.mo-nav-link.is-active {
  color: var(--mo-accent);
  background: var(--mo-accent-dim);
}

.mo-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mo-user {
  color: var(--mo-text-muted);
  font-family: var(--mo-font-mono);
  font-size: 12px;
}

.mo-main {
  flex: 1;
  overflow: auto;
  min-height: 0;
}
</style>
