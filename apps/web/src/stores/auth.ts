import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const TOKEN_KEY = 'mo_token'
const USER_KEY = 'mo_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const username = ref<string | null>(localStorage.getItem(USER_KEY))

  const isAuthenticated = computed(() => Boolean(token.value))

  /** 假登录：任意非空账号密码即可，写入 localStorage */
  function login(account: string, _password: string) {
    const fakeToken = `mo-demo-${Date.now()}`
    token.value = fakeToken
    username.value = account
    localStorage.setItem(TOKEN_KEY, fakeToken)
    localStorage.setItem(USER_KEY, account)
  }

  function logout() {
    token.value = null
    username.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return {
    token,
    username,
    isAuthenticated,
    login,
    logout,
  }
})
