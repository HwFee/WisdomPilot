/**
 * API Client - Base client with auth handling
 */

import { ApiError } from '@/types/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const REQUEST_TIMEOUT = 30000 // 30 seconds

/**
 * Fetch with authentication header and timeout
 */
export async function fetchWithAuth(
  url: string,
  token: string,
  options: RequestInit = {}
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)

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

    if (!response.ok) {
      const data = await response.json()
      const error = new Error((data as ApiError).detail || 'API request failed')
      ;(error as Error & { status?: number }).status = response.status
      throw error
    }

    return response
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
export async function post<T>(endpoint: string, token: string, body?: unknown): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  })
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
