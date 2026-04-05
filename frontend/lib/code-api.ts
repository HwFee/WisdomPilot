const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface CodeExecutionRequest {
  code: string
  language_id: number
  stdin?: string
}

export interface CodeExecutionResponse {
  token: string
  status: string
  status_id: number
  stdout: string | null
  stderr: string | null
  compile_output: string | null
  message: string | null
  time: string | null
  memory: number | null
  exit_code: number | null
}

export interface SupportedLanguage {
  id: number
  name: string
  monaco_language: string
}

// Language configurations for frontend
export const LANGUAGE_CONFIG: Record<number, { label: string; monacoLanguage: string }> = {
  71: { label: 'Python', monacoLanguage: 'python' },
  63: { label: 'JavaScript', monacoLanguage: 'javascript' },
  74: { label: 'TypeScript', monacoLanguage: 'typescript' },
  50: { label: 'C', monacoLanguage: 'c' },
  54: { label: 'C++', monacoLanguage: 'cpp' },
}

async function fetchWithAuth(url: string, token: string, options: RequestInit = {}): Promise<Response> {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'API request failed')
  }

  return response
}

export async function executeCode(
  token: string,
  request: CodeExecutionRequest
): Promise<CodeExecutionResponse> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/code/execute`, token, {
    method: 'POST',
    body: JSON.stringify(request),
  })
  return response.json()
}

export async function getSupportedLanguages(
  token: string
): Promise<SupportedLanguage[]> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/code/languages`, token)
  return response.json()
}
