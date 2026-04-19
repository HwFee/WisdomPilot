/**
 * API Client - Base client with auth handling
 */

import { ApiError } from '@/types/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const REQUEST_TIMEOUT = 30000 // 30 seconds for regular requests
const CODE_EXECUTION_TIMEOUT = 60000 // 60 seconds for code execution (Judge0 can be slow)

/**
 * Fetch with authentication header and timeout
 */
export async function fetchWithAuth(
  url: string,
  token: string,
  options: RequestInit = {},
  timeout?: number
): Promise<Response> {
  const requestTimeout = timeout || REQUEST_TIMEOUT
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), requestTimeout)

  // [DEBUG] API 请求日志
  console.log('[API] 发起请求:', {
    url,
    method: options.method || 'GET',
    hasToken: !!token,
    tokenPreview: token ? `${token.substring(0, 10)}...` : 'null',
  })

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        ...options.headers,
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    })

    // [DEBUG] API 响应日志
    console.log('[API] 响应状态:', {
      url,
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
    })

    if (!response.ok) {
      let errorMessage = 'API request failed'
      try {
        const data = await response.json()
        errorMessage = (data as ApiError).detail || errorMessage
        console.error('[API] 请求失败:', {
          url,
          status: response.status,
          error: data,
        })
      } catch {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`
        console.error('[API] 请求失败:', {
          url,
          status: response.status,
          statusText: response.statusText,
        })
      }
      const error = new Error(errorMessage)
      ;(error as Error & { status?: number }).status = response.status
      throw error
    }

    return response
  } catch (error) {
    // [DEBUG] 网络错误日志
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('[API] 请求超时:', { url, timeout: REQUEST_TIMEOUT })
    } else if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error('[API] 网络错误 - 无法连接到后端:', {
        url,
        API_BASE_URL,
        hint: '请确认后端是否正在运行 (python -m uvicorn app.main:app --host 0.0.0.0 --port 8000)',
      })
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

/**
 * GET request with auth
 */
export async function get<T>(endpoint: string, token: string): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token)
  return response.json()
}

/**
 * POST request with auth
 */
export async function post<T>(endpoint: string, token: string, body?: unknown, timeout?: number): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  }, timeout)
  return response.json()
}

/**
 * PUT request with auth
 */
export async function put<T>(endpoint: string, token: string, body?: unknown): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token, {
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  })
  return response.json()
}

/**
 * PATCH request with auth
 */
export async function patch<T>(endpoint: string, token: string, body?: unknown): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token, {
    method: 'PATCH',
    body: body ? JSON.stringify(body) : undefined,
  })
  return response.json()
}

/**
 * DELETE request with auth
 */
export async function del<T>(endpoint: string, token: string): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token, {
    method: 'DELETE',
  })
  return response.json()
}

/**
 * POST request without auth (for login/register)
 */
export async function postPublic<T>(endpoint: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error((data as ApiError).detail || 'Request failed')
  }

  return data as T
}

export { API_BASE_URL }
