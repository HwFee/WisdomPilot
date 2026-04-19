/**
 * AI API - AI-powered features endpoints
 */

import {
  ChoiceExplanationRequest,
  ChoiceExplanationResponse,
  CodeReviewRequest,
  CodeReviewResponse,
  AIChatRequest,
  AIChatResponse,
  ChoiceAnalysisRequest,
  ChoiceAnalysisResponse,
  CodeFeedbackRequest,
  CodeFeedbackResponse,
  AIConfigResponse,
  UpdateAIConfigRequest,
  AIStatusResponse,
  TestConnectionRequest,
  TestConnectionResponse,
} from '@/types/api'
import { get, post, put } from './client'

// ========================================
// AI Choice Explanation
// ========================================

export async function getChoiceExplanation(
  request: ChoiceExplanationRequest,
  token: string
): Promise<ChoiceExplanationResponse> {
  return post<ChoiceExplanationResponse>('/api/ai/choice-explanation', token, request)
}

// ========================================
// AI Code Review
// ========================================

export async function getCodeReview(
  request: CodeReviewRequest,
  token: string
): Promise<CodeReviewResponse> {
  return post<CodeReviewResponse>('/api/ai/code-review', token, request)
}

// ========================================
// AI Chat
// ========================================

export async function aiChat(
  request: AIChatRequest,
  token: string
): Promise<AIChatResponse> {
  return post<AIChatResponse>('/api/ai/chat', token, request)
}

export async function aiChatStream(
  request: { message: string; context?: Record<string, unknown> },
  token: string,
  onChunk: (content: string) => void,
  onError: (error: string) => void,
  onComplete: () => void
): Promise<void> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const data = await response.json()
    onError(data.detail || 'Chat stream failed')
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    onError('No response stream')
    return
  }

  const decoder = new TextDecoder()

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            onComplete()
            return
          }
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) {
              onError(parsed.error)
            } else if (parsed.content) {
              onChunk(parsed.content)
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
    onComplete()
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Stream error')
  }
}

// ========================================
// AI Analysis (embedded in exercise pages)
// ========================================

export async function analyzeChoice(
  request: ChoiceAnalysisRequest,
  token: string
): Promise<ChoiceAnalysisResponse> {
  return post<ChoiceAnalysisResponse>('/api/ai/choice-analysis', token, request)
}

export async function getCodeFeedback(
  request: CodeFeedbackRequest,
  token: string
): Promise<CodeFeedbackResponse> {
  return post<CodeFeedbackResponse>('/api/ai/code-feedback', token, request)
}

// ========================================
// AI Config (Admin only)
// ========================================

export async function getAIConfig(token: string): Promise<AIConfigResponse> {
  return get<AIConfigResponse>('/api/admin/ai/config', token)
}

export async function updateAIConfig(
  request: UpdateAIConfigRequest,
  token: string
): Promise<{ message: string }> {
  return put<{ message: string }>('/api/admin/ai/config', token, request)
}

export async function getAIStatus(token: string): Promise<AIStatusResponse> {
  return get<AIStatusResponse>('/api/admin/ai/status', token)
}

export async function testAIConnection(
  request: TestConnectionRequest,
  token: string
): Promise<TestConnectionResponse> {
  return post<TestConnectionResponse>('/api/admin/ai/test-connection', token, request)
}

// ========================================
// AI Exercise Hint (挑战之路使用)
// ========================================

export interface ExerciseHintRequest {
  exercise_title: string
  exercise_description: string
  difficulty: number
  knowledge_points: string[]
  hint_level: 'light' | 'medium' | 'deep'
  code_template?: string
  sample_input?: string
  sample_output?: string
}

export async function streamExerciseHint(
  request: ExerciseHintRequest,
  token: string,
  onChunk: (content: string) => void,
  onError: (error: string) => void,
  onComplete: () => void
): Promise<void> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/ai/exercise-hint/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const data = await response.json()
    onError(data.detail || 'AI 提示请求失败')
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    onError('无响应流')
    return
  }

  const decoder = new TextDecoder()

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            onComplete()
            return
          }
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) {
              onError(parsed.error)
            } else if (parsed.content) {
              onChunk(parsed.content)
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
    onComplete()
  } catch (error) {
    onError(error instanceof Error ? error.message : '流式输出错误')
  }
}

// Re-export types
export type {
  ChoiceExplanationRequest,
  ChoiceExplanationResponse,
  CodeReviewRequest,
  CodeReviewResponse,
  AIChatRequest,
  AIChatResponse,
  ChoiceAnalysisRequest,
  ChoiceAnalysisResponse,
  CodeFeedbackRequest,
  CodeFeedbackResponse,
  AIConfigResponse,
  UpdateAIConfigRequest,
  AIStatusResponse,
  TestConnectionRequest,
  TestConnectionResponse,
}
