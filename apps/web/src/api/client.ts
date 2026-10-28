import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

/**
 * baseURL ← VITE_API_BASE。
 * 开发默认可用相对路径 /api/v1 + vite proxy，避免直连 :8000 CORS。
 * .env.example 仍记录直连形态 http://localhost:8000/api/v1。
 */
const baseURL = import.meta.env.VITE_API_BASE || '/api/v1'

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
      localStorage.removeItem('mo_user')
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

export async function put<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await apiClient.put<T>(url, body, config)
  return data
}

export async function del<T = void>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await apiClient.delete<T>(url, config)
  return data
}

export default apiClient
