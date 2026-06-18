export const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL
  if (configured) return configured

  // During development in the browser, use a relative path so Next.js rewrites
  // proxy API calls through the frontend origin. This avoids CORS issues caused
  // by some browsers or network environments stripping CORS response headers.
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    return ''
  }

  return DEFAULT_API_BASE_URL
}
