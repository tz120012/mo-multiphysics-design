import type { AuthUser, LoginRequest, LoginResponse } from './types'

const NOT_WIRED = 'not wired'

/** POST /auth/login — 相对 baseURL（含 /api/v1） */
export async function login(_body: LoginRequest): Promise<LoginResponse> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** POST /auth/logout → 204 */
export async function logout(): Promise<void> {
  return Promise.reject(new Error(NOT_WIRED))
}

/** GET /auth/me */
export async function getMe(): Promise<AuthUser> {
  return Promise.reject(new Error(NOT_WIRED))
}
