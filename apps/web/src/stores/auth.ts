import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'

const TOKEN_KEY = 'mo_token'
const USER_KEY = 'mo_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const username = ref<string | null>(localStorage.getItem(USER_KEY))

  const isAuthenticated = computed(() => Boolean(token.value))

  function persist(accessToken: string, user: string) {
    token.value = accessToken
    username.value = user
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, user)
  }

  function clearLocal() {
    token.value = null
    username.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  /** 真登录：POST /auth/login，写入 accessToken */
  async function login(user: string, password: string) {
    const res = await authApi.login({ username: user, password })
    persist(res.accessToken, user)
    try {
      const me = await authApi.getMe()
      if (me.username) {
        username.value = me.username
        localStorage.setItem(USER_KEY, me.username)
      }
    } catch {
      // /me 失败不阻断登录；已有 token
    }
  }

  /** 登出：尽量调 API，无论成败清本地 */
  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // ignore
    } finally {
      clearLocal()
    }
  }

  return {
    token,
    username,
    isAuthenticated,
    login,
    logout,
  }
})
