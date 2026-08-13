/* ============================================
   训练舱 · 契约层客户端
   USE_MOCK=1（默认）：全部走本地 mock，用于后端未就绪期
   USE_MOCK=0：走真实后端，错误向上抛出由页面降级显示
   切换方式：.env.local 里 NEXT_PUBLIC_DECK_MOCK=0
   ============================================ */

import { API_BASE_URL } from '../client'
import { getStoredToken } from '../auth'

export const USE_MOCK = process.env.NEXT_PUBLIC_DECK_MOCK !== '0'

export class DeckApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'DeckApiError'
    this.status = status
  }
}

/** 性能审计修复：同 URL+方法 的 in-flight 请求去重，避免 DeckHeader 与页面组件重复请求同一聚合接口 */
const IN_FLIGHT = new Map<string, Promise<unknown>>()

function inflightKey(path: string, init?: RequestInit): string {
  return `${init?.method ?? 'GET'} ${path}`
}

/** 真实后端请求封装：带 token、30s 超时、in-flight 去重，非 2xx 抛 DeckApiError（401 由页面守卫处理） */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const key = inflightKey(path, init)
  const cached = IN_FLIGHT.get(key) as Promise<T> | undefined
  if (cached) return cached

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30_000)
  const run = (async () => {
    const token = getStoredToken()
    const apiPath = path.startsWith('/api') ? path : `/api${path}`
    try {
      const res = await fetch(`${API_BASE_URL}${apiPath}`, {
        ...init,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(init?.headers ?? {}),
        },
      })
      if (!res.ok) {
        throw new DeckApiError(`请求失败：${path}（${res.status}）`, res.status)
      }
      return (await res.json()) as T
    } finally {
      clearTimeout(timeoutId)
      IN_FLIGHT.delete(key)
    }
  })()
  IN_FLIGHT.set(key, run)
  return run
}

/** mock 模式下的模拟网络延迟，让加载/动效可见（仅开发模式） */
export function mockDelay(ms = 200): Promise<void> {
  if (process.env.NODE_ENV !== 'development') return Promise.resolve()
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * 域 API 的统一入口：mock 模式直接返回 mock()，否则请求真实后端。
 * 每个 lib/api/deck/*.ts 的导出函数都应通过它实现。
 */
export async function deckCall<T>(path: string, mock: () => T | Promise<T>, init?: RequestInit): Promise<T> {
  if (USE_MOCK) {
    await mockDelay()
    return mock()
  }
  return apiFetch<T>(path, init)
}
