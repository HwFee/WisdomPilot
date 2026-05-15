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
// AI 配置管理（管理员）
// ========================================

export interface AIConfigResponse {
  provider: string
  model: string
  temperature: number
  is_configured: boolean
  has_api_key: boolean
  api_key_preview?: string  // 如 "sk-cp****abcd"
  api_key_length?: number
  connection_status?: string
  connection_address?: string
  is_local_first: boolean
}

export interface UpdateAIConfigRequest {
  provider?: string
  api_key?: string
  model?: string
  temperature?: number
  base_url?: string
  local_base_url?: string
  is_local_first?: boolean
}

// ========================================
// AI Provider Status
// ========================================

export interface ProviderStatus {
  type: string
  address: string
  status: 'connected' | 'disconnected' | 'unknown'
  model?: string
  available_models?: string[]
}

export interface AIStatusResponse {
  current_provider: string
  current_model: string
  is_local_first: boolean
  providers: ProviderStatus[]
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

// ========================================
// AI 选择题分析 —— 错题触发
// ========================================

export interface ChoiceAnalysisRequest {
  question_text: string
  options: string[]
  user_selected: number
  correct_answer: number
  chapter_id: number
  exercise_id: string
}

export interface ChoiceAnalysisResponse {
  analysis: string
  is_correct: boolean
}

export async function getChoiceAnalysis(
  token: string,
  request: ChoiceAnalysisRequest
): Promise<ChoiceAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/choice-analysis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || '获取 AI 分析失败')
  }

  return response.json()
}

// ========================================
// AI 编程题反馈 —— 纠错 + 优化 + 建议 三合一
// ========================================

export interface CodeFeedbackRequest {
  code: string
  language: string
  exercise_description: string
  expected_output: string
  actual_output?: string
  status?: string
  error_message?: string
  chapter_id: number
  exercise_id: string
}

export interface CodeFeedbackResponse {
  diagnosis: string
  suggestions: string
  optimized_code: string
}

export async function getCodeFeedback(
  token: string,
  request: CodeFeedbackRequest
): Promise<CodeFeedbackResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/code-feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || '获取 AI 反馈失败')
  }

  return response.json()
}

// ========================================
// AI Provider Status
// ========================================

export async function getAIStatus(token: string): Promise<AIStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/admin/ai/status`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || '获取 AI 状态失败')
  }

  return response.json()
}

// ========================================
// Test Connection
// ========================================

export interface TestConnectionRequest {
  provider: 'deepseek' | 'siliconflow' | 'minimax' | 'ollama' | 'lmstudio'
  api_key?: string
  model?: string
  base_url?: string
  local_base_url?: string
}

export interface TestConnectionResponse {
  success: boolean
  message: string
  model?: string
  address?: string
  latency_ms?: number
}

export async function testAIConnection(
  token: string,
  request: TestConnectionRequest
): Promise<TestConnectionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/admin/ai/test-connection`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || '测试连接失败')
  }

  return response.json()
}
