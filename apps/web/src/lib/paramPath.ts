/** 读写 geometry params 点路径（如 `rotor.poleCount`）。 */

export function getPath(root: unknown, path: string): unknown {
  if (!path) return root
  const parts = path.split('.')
  let cur: unknown = root
  for (const part of parts) {
    if (cur == null || typeof cur !== 'object') return undefined
    cur = (cur as Record<string, unknown>)[part]
  }
  return cur
}

export function setPath(root: Record<string, unknown>, path: string, value: unknown): void {
  const parts = path.split('.')
  let cur: Record<string, unknown> = root
  for (let i = 0; i < parts.length - 1; i++) {
    const key = parts[i]
    const next = cur[key]
    if (next == null || typeof next !== 'object' || Array.isArray(next)) {
      const created: Record<string, unknown> = {}
      cur[key] = created
      cur = created
    } else {
      cur = next as Record<string, unknown>
    }
  }
  cur[parts[parts.length - 1]] = value
}

export function cloneJson<T>(value: T): T {
  return structuredClone(value)
}
