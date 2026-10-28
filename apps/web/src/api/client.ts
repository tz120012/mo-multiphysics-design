import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

/** 契约 servers.url 为相对路径 /api/v1；本地默认拼到 FastAPI 根 */
const baseURL = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'

/**
 * HTTP 客户端占位封装。
 * baseURL 读取 VITE_API_BASE（默认含 /api/v1）；
 * 业务路径用 /auth/login、/projects 等相对路径，不再叠一层 /api/v1。
 * 鉴权 token 从 localStorage 注入。Q1 阶段列表仍用本地假数据。
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('mo_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('mo_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await apiClient.get<T>(url, config)
  return data
}

export async function post<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await apiClient.post<T>(url, body, config)
  return data
}

export default apiClient
