/**
 * API Client - Base client with auth handling
 */

import { ApiError } from "@/types/api";
import { getApiBaseUrl } from "@/lib/api-config";

function normalizeApiBaseUrl(rawUrl: string): string {
  const trimmed = rawUrl.replace(/\/+$/, "");
  return trimmed.endsWith("/api") ? trimmed.slice(0, -4) : trimmed;
}

const API_BASE_URL = normalizeApiBaseUrl(
  getApiBaseUrl(),
);
const REQUEST_TIMEOUT = 30000; // 30 seconds for regular requests
const CODE_EXECUTION_TIMEOUT = 60000; // 60 seconds for code execution (Judge0 can be slow)

/**
 * Fetch with authentication header and timeout
 */
export async function fetchWithAuth(
  url: string,
  token: string,
  options: RequestInit = {},
  timeout?: number,
): Promise<Response> {
  const requestTimeout = timeout || REQUEST_TIMEOUT;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), requestTimeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        ...options.headers,
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // 401: token过期或无效，清除登录状态并跳转
      if (response.status === 401) {
        localStorage.removeItem("token:v1");
        localStorage.removeItem("user:v1");
        window.location.href = "/login";
        throw new Error("登录已过期，请重新登录");
      }

      // 尝试解析错误响应体
      let data: unknown = {};
      try {
        const text = await response.text();
        if (text) {
          data = JSON.parse(text);
        }
      } catch {
        // 响应体不是有效的 JSON，保持空对象
      }

      const errorDetail =
        (data as ApiError)?.detail ||
        response.statusText ||
        `API request failed with status ${response.status}`;
      const error = new Error(errorDetail);
      (error as Error & { status?: number }).status = response.status;
      throw error;
    }

    return response;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`Request timeout after ${requestTimeout}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * GET request with auth
 */
export async function get<T>(endpoint: string, token: string): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token);
  return response.json();
}

/**
 * POST request with auth
 */
export async function post<T>(
  endpoint: string,
  token: string,
  body?: unknown,
  timeout?: number,
): Promise<T> {
  const response = await fetchWithAuth(
    `${API_BASE_URL}${endpoint}`,
    token,
    {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    },
    timeout,
  );
  return response.json();
}

/**
 * PUT request with auth
 */
export async function put<T>(
  endpoint: string,
  token: string,
  body?: unknown,
): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
  return response.json();
}

/**
 * PATCH request with auth
 */
export async function patch<T>(
  endpoint: string,
  token: string,
  body?: unknown,
): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token, {
    method: "PATCH",
    body: body ? JSON.stringify(body) : undefined,
  });
  return response.json();
}

/**
 * DELETE request with auth
 */
export async function del<T>(endpoint: string, token: string): Promise<T> {
  const response = await fetchWithAuth(`${API_BASE_URL}${endpoint}`, token, {
    method: "DELETE",
  });
  return response.json();
}

/**
 * POST request without auth (for login/register)
 */
export async function postPublic<T>(
  endpoint: string,
  body: unknown,
  timeout: number = REQUEST_TIMEOUT,
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    // 尝试解析响应体
    let data: unknown = {};
    try {
      const text = await response.text();
      if (text) {
        data = JSON.parse(text);
      }
    } catch {
      // 响应体不是有效的 JSON，保持空对象
    }

    if (!response.ok) {
      const errorDetail =
        (data as ApiError)?.detail ||
        response.statusText ||
        `Request failed with status ${response.status}`;
      throw new Error(errorDetail);
    }

    return data as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`Request timeout after ${timeout}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * POST request with keepalive=true — survives page navigation/unmount.
 * Use this for fire-and-forget cleanup requests (e.g. session end on unmount).
 * Does NOT use AbortController so it won't be cancelled by timeouts.
 */
export function postKeepalive(
  endpoint: string,
  token: string,
  body?: unknown,
): void {
  const url = `${API_BASE_URL}${endpoint}`;
  const payload = body ? JSON.stringify(body) : undefined;

  fetch(url, {
    method: "POST",
    keepalive: true,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: payload,
  }).catch(() => {});
}

export { API_BASE_URL, normalizeApiBaseUrl };
