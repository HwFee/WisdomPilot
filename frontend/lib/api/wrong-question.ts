/**
 * Wrong Question API - 错题收集接口
 */

import { post } from './client'

// 错题收集请求
export interface CollectWrongQuestionRequest {
  exercise_key: string // 格式：chapterId-subsectionIndex-exerciseId 或 arena-sessionId-exerciseId
  user_answer: unknown // 用户答案
  course_id: number // 课程ID
  chapter_id?: number // 章节ID
  exercise_id?: number // 练习题ID（可选）
  exercise_content?: Record<string, unknown> // 题目内容快照
  exercise_type: string // 题目类型
  knowledge_points?: string[] // 知识点列表
}

// 错题收集响应
export interface CollectWrongQuestionResponse {
  id: string
  exercise_key: string
  error_count: number
  is_resolved: boolean
  message: string
}

/**
 * 收集错题（前端硬编码习题）
 *
 * 当前端使用硬编码习题（非数据库 Exercise）时，使用此函数收集错题。
 * exercise_key 格式：chapterId-subsectionIndex-exerciseId
 */
export async function collectWrongQuestion(
  token: string,
  data: CollectWrongQuestionRequest
): Promise<CollectWrongQuestionResponse> {
  console.log('[错题收集] 发起请求:', data)

  try {
    const result = await post<CollectWrongQuestionResponse>(
      '/api/review/wrong-questions/collect',
      token,
      data
    )
    console.log('[错题收集] 成功:', result)
    return result
  } catch (error) {
    console.error('[错题收集] 失败:', error)
    throw error
  }
}

/**
 * 标记错题已解决
 *
 * 当用户答对曾经错过的题目时调用此函数。
 */
export async function resolveWrongQuestion(
  token: string,
  exerciseId: number
): Promise<{ success: boolean; message: string }> {
  console.log('[错题解决] 发起请求:', { exerciseId })

  try {
    const result = await post<{ success: boolean; message: string }>(
      `/api/review/wrong-questions/${exerciseId}/resolve`,
      token,
      {}
    )
    console.log('[错题解决] 成功:', result)
    return result
  } catch (error) {
    console.error('[错题解决] 失败:', error)
    throw error
  }
}
