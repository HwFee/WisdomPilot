const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ========================================
// AI 选择题解答
// ========================================

export interface ChoiceExplanationRequest {
  chapter_id: number
  subsection_index: number
  exercise_id: number
  question: string
  options: string[]
  user_selected_index: number
  correct_index: number
}

export interface ChoiceExplanationResponse {
  explanation: string
}

export async function getChoiceExplanation(
  token: string,
  request: ChoiceExplanationRequest
): Promise<ChoiceExplanationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/choice-explanation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || '获取 AI 解答失败')
  }

  return response.json()
}

// ========================================
// AI 代码审查
// ========================================

export interface CodeReviewRequest {
  code: string
  language: string
  chapter_id?: number
  subsection_index?: number
}

export interface CodeReviewResponse {
  review: string
  score?: number
  suggestions?: string[]
}

export async function getCodeReview(
  token: string,
  request: CodeReviewRequest
): Promise<CodeReviewResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/code-review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || '代码审查失败')
  }

  return response.json()
}

// ========================================
// AI 配置管理（管理员）
// ========================================

export interface AIConfigResponse {
  provider: string
  model: string
  temperature: number
  is_configured: boolean
}

export interface UpdateAIConfigRequest {
  provider?: string
  api_key?: string
  model?: string
  temperature?: number
  base_url?: string
}

export async function getAIConfig(token: string): Promise<AIConfigResponse> {
  const response = await fetch(`${API_BASE_URL}/api/admin/ai/config`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || '获取 AI 配置失败')
  }

  return response.json()
}

export async function updateAIConfig(
  token: string,
  request: UpdateAIConfigRequest
): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/admin/ai/config`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || '更新 AI 配置失败')
  }

  return response.json()
}
