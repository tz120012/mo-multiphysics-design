/**
 * history/stack.json 序列化（对齐 docs/drafts/history-契约-q1-6.md §4）
 * Q1：工具函数 + 空栈启动；mems PUT 接线后可挂 serialize → zip。
 */
import {
  HISTORY_STACK_SCHEMA_VERSION,
  type HistoryEntry,
  type HistoryStackDocument,
} from '@/api/types'

export const EMPTY_HISTORY_STACK: HistoryStackDocument = {
  schemaVersion: HISTORY_STACK_SCHEMA_VERSION,
  entries: [],
  cursor: 0,
}

export function serializeHistoryStack(
  entries: HistoryEntry[],
  cursor: number,
): HistoryStackDocument {
  const len = entries.length
  const c = Math.max(0, Math.min(cursor, len))
  return {
    schemaVersion: HISTORY_STACK_SCHEMA_VERSION,
    entries: entries.map((e) => ({ ...e })),
    cursor: c,
  }
}

/**
 * 反序列化；缺文件 / 非法时回空栈（允许样例包无 history/）。
 */
export function deserializeHistoryStack(raw: unknown): HistoryStackDocument {
  if (raw == null || typeof raw !== 'object') {
    return { ...EMPTY_HISTORY_STACK, entries: [] }
  }
  const obj = raw as Record<string, unknown>
  const entries = Array.isArray(obj.entries)
    ? (obj.entries as HistoryEntry[]).filter(
        (e) => e && typeof e === 'object' && typeof e.id === 'string',
      )
    : []
  let cursor = typeof obj.cursor === 'number' && Number.isFinite(obj.cursor) ? obj.cursor : 0
  cursor = Math.max(0, Math.min(Math.floor(cursor), entries.length))
  return {
    schemaVersion:
      typeof obj.schemaVersion === 'string' ? obj.schemaVersion : HISTORY_STACK_SCHEMA_VERSION,
    entries,
    cursor,
  }
}

/** 挂点注释：保存工程时 → serializeHistoryStack → 写入 mems zip 的 history/stack.json */
export function historyStackJsonPath(): string {
  return 'history/stack.json'
}
