import { apiClient } from './client'
import type { AuthUser, LoginRequest, LoginResponse } from './types'

/** POST /auth/login — body { username, password } */
export async function login(body: LoginRequest): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login', body)
  return data
}

/** POST /auth/logout → 204 */
export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

/** GET /auth/me */
export async function getMe(): Promise<AuthUser> {
  const { data } = await apiClient.get<AuthUser>('/auth/me')
  return data
}
