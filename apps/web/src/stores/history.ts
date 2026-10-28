import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { HistoryEntry, HistoryListResponse, HistoryStackDocument } from '@/api/types'
import {
  deserializeHistoryStack,
  serializeHistoryStack,
} from '@/lib/historyStack'

function newId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `hist_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
}

export type PushCommandInput = {
  commandType: string
  summary: string
  payload: Record<string, unknown>
  inverse?: Record<string, unknown>
}

/**
 * Q1-6 客户端权威线性命令栈（local-first）。
 * 契约：docs/drafts/history-契约-q1-6.md
 *
 * 不变量：0 <= cursor <= entries.length
 * - undo：cursor>0 → cursor--，apply inverse of entries[cursor]
 * - redo：cursor<len → apply entries[cursor]，cursor++
 * - 新命令：entries.splice(cursor) 截断 redo 尾，push，cursor=length
 *
 * UI 只跟本地栈；不要等 POST history/undo|redo。
 * 样例 fixture 切换时由 Workspace 调用 clear()。
 */
export const useHistoryStore = defineStore('history', () => {
  const entries = ref<HistoryEntry[]>([])
  const cursor = ref(0)

  const canUndo = computed(() => cursor.value > 0)
  const canRedo = computed(() => cursor.value < entries.value.length)

  /** 形状对齐 HistoryListResponse */
  const list = computed<HistoryListResponse>(() => ({
    entries: entries.value,
    cursor: cursor.value,
  }))

  function push(input: PushCommandInput): HistoryEntry {
    // 截断 redo 尾
    entries.value.splice(cursor.value)
    const entry: HistoryEntry = {
      id: newId(),
      commandType: input.commandType,
      summary: input.summary,
      createdAt: new Date().toISOString(),
      payload: input.payload,
      ...(input.inverse !== undefined ? { inverse: input.inverse } : {}),
    }
    entries.value.push(entry)
    cursor.value = entries.value.length
    return entry
  }

  /**
   * 撤销：cursor--，返回 entries[cursor]（调用方 apply inverse / payload.before）
   */
  function undo(): HistoryEntry | null {
    if (cursor.value <= 0) return null
    cursor.value -= 1
    return entries.value[cursor.value] ?? null
  }

  /**
   * 重做：返回 entries[cursor]，再 cursor++（调用方 apply payload）
   */
  function redo(): HistoryEntry | null {
    if (cursor.value >= entries.value.length) return null
    const entry = entries.value[cursor.value] ?? null
    if (!entry) return null
    cursor.value += 1
    return entry
  }

  function clear() {
    entries.value = []
    cursor.value = 0
  }

  /** 从 history/stack.json 恢复；缺文件时用空栈 */
  function loadStack(doc: unknown) {
    const parsed = deserializeHistoryStack(doc)
    entries.value = parsed.entries
    cursor.value = parsed.cursor
  }

  /** 导出落盘文档（mems PUT 挂点） */
  function toStackDocument(): HistoryStackDocument {
    return serializeHistoryStack(entries.value, cursor.value)
  }

  return {
    entries,
    cursor,
    canUndo,
    canRedo,
    list,
    push,
    undo,
    redo,
    clear,
    loadStack,
    toStackDocument,
  }
})
