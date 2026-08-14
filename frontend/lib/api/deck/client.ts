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

/** 性能审计修复：同 GET URL 的 in-flight 请求去重，避免 DeckHeader 与页面组件重复请求同一聚合接口。
 *  安全审计修复：仅对 GET 去重——POST 请求体不同不能复用响应，去重键不含 body
 *  会让不同 body 的并发 POST 静默丢请求且张冠李戴。 */
const IN_FLIGHT = new Map<string, Promise<unknown>>()

/** 默认 30s 超时；导师 LLM 端点后端最坏 ~366s（两次串行调用 × 3 重试 × 60s+退避），
 *  用长超时避免前端 abort 后后端仍在烧 LLM 费用。 */
const DEFAULT_TIMEOUT_MS = 30_000
const LLM_TIMEOUT_MS = 300_000

/** 真实后端请求封装：带 token、超时、GET in-flight 去重，非 2xx 抛 DeckApiError（401 清登录态并跳转登录页） */
export async function apiFetch<T>(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const method = init?.method ?? 'GET'
  const key = `${method} ${path}`
  const cached = IN_FLIGHT.get(key) as Promise<T> | undefined
  if (method === 'GET' && cached) return cached

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
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
        // 401：token 过期/失效，清除登录状态并跳转（对齐 lib/api/client.ts 的行为）
        if (res.status === 401) {
          localStorage.removeItem('token:v1')
          localStorage.removeItem('user:v1')
          window.location.href = '/login'
          throw new DeckApiError('登录已过期，请重新登录', res.status)
        }
        throw new DeckApiError(`请求失败：${path}（${res.status}）`, res.status)
      }
      return (await res.json()) as T
    } finally {
      clearTimeout(timeoutId)
      IN_FLIGHT.delete(key)
    }
  })()
  if (method === 'GET') IN_FLIGHT.set(key, run)
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
 * timeoutMs 透传给 apiFetch（默认 30s；导师 LLM 端点传长超时）。
 */
export async function deckCall<T>(
  path: string,
  mock: () => T | Promise<T>,
  init?: RequestInit,
  timeoutMs?: number
): Promise<T> {
  if (USE_MOCK) {
    await mockDelay()
    return mock()
  }
  return apiFetch<T>(path, init, timeoutMs)
}

export { LLM_TIMEOUT_MS }
