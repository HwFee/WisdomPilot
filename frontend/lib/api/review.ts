/**
 * Review API - 复习系统接口
 */

import {
  ReviewQueueResponse,
  ReviewQueueItem,
  CompleteReviewRequest,
  CompleteReviewResponse,
  TargetPracticeRequest,
  TargetPracticeResponse,
  WeakPointListResponse,
  WeakPointResponse,
  ReviewStatsResponse,
  WrongQuestionListResponse,
  WrongQuestionResponse,
  WeakPointAnalysisResponse,
  KnowledgePointAnalysis,
  EnhancedTargetPracticeRequest,
  EnhancedTargetPracticeResponse,
  ReviewReminderResponse,
  SpacedRepetitionResponse,
} from '@/types/review'
import { get, post } from './client'

// ========================================
// Review Queue API Functions
// ========================================

export async function getReviewQueue(
  token: string,
  limit: number = 10
): Promise<ReviewQueueResponse> {
  return get<ReviewQueueResponse>(`/api/review/queue?limit=${limit}`, token)
}

export async function completeReview(
  exerciseId: number,
  request: CompleteReviewRequest,
  token: string
): Promise<CompleteReviewResponse> {
  return post<CompleteReviewResponse>(
    `/api/review/complete/${exerciseId}`,
    token,
    request
  )
}

// ========================================
// Weak Points API Functions
// ========================================

export async function getWeakPoints(
  token: string,
  courseId?: number,
  limit: number = 20
): Promise<WeakPointListResponse> {
  const params = new URLSearchParams()
  if (courseId) params.append('course_id', String(courseId))
  params.append('limit', String(limit))
  return get<WeakPointListResponse>(`/api/review/weak-points?${params}`, token)
}

export async function getTargetPractice(
  request: TargetPracticeRequest,
  token: string
): Promise<TargetPracticeResponse> {
  return post<TargetPracticeResponse>('/api/review/weak-points/target', token, request)
}

// ========================================
// Review Stats API Functions
// ========================================

export async function getReviewStats(
  token: string
): Promise<ReviewStatsResponse> {
  return get<ReviewStatsResponse>('/api/review/stats', token)
}

// ========================================
// Wrong Questions API Functions
// ========================================

export async function getWrongQuestions(
  token: string,
  params?: {
    course_id?: number
    chapter_id?: number
    is_resolved?: boolean
    limit?: number
    offset?: number
  }
): Promise<WrongQuestionListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.course_id) searchParams.append('course_id', String(params.course_id))
  if (params?.chapter_id) searchParams.append('chapter_id', String(params.chapter_id))
  if (params?.is_resolved !== undefined) searchParams.append('is_resolved', String(params.is_resolved))
  if (params?.limit) searchParams.append('limit', String(params.limit))
  if (params?.offset) searchParams.append('offset', String(params.offset))

  const queryString = searchParams.toString()
  const url = queryString ? `/api/review/wrong-questions?${queryString}` : '/api/review/wrong-questions'
  return get<WrongQuestionListResponse>(url, token)
}

export async function getWrongQuestion(
  wrongQuestionId: string,
  token: string
): Promise<WrongQuestionResponse> {
  return get<WrongQuestionResponse>(`/api/review/wrong-questions/${wrongQuestionId}`, token)
}

export async function deleteWrongQuestion(
  wrongQuestionId: string,
  token: string
): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/review/wrong-questions/${wrongQuestionId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw new Error(`Failed to delete wrong question: ${response.statusText}`)
  }
  return response.json()
}

// ========================================
// Analysis API Functions
// ========================================

export async function getWeakPointsAnalysis(
  token: string,
  courseId?: number,
  limit: number = 20
): Promise<WeakPointAnalysisResponse> {
  const params = new URLSearchParams()
  if (courseId) params.append('course_id', String(courseId))
  params.append('limit', String(limit))
  return get<WeakPointAnalysisResponse>(`/api/review/analysis/weak-points?${params}`, token)
}

// ========================================
// Enhanced Practice API Functions
// ========================================

export async function getEnhancedTargetPractice(
  request: EnhancedTargetPracticeRequest,
  token: string
): Promise<EnhancedTargetPracticeResponse> {
  return post<EnhancedTargetPracticeResponse>('/api/review/practice/enhanced', token, request)
}

// ========================================
// Review Reminder API Functions
// ========================================

export async function getReviewReminders(
  token: string
): Promise<ReviewReminderResponse> {
  return get<ReviewReminderResponse>('/api/review/reminders', token)
}

// Re-export types
export type {
  ReviewQueueResponse,
  ReviewQueueItem,
  CompleteReviewResponse,
  TargetPracticeResponse,
  WeakPointListResponse,
  WeakPointResponse,
  ReviewStatsResponse,
  WrongQuestionListResponse,
  WrongQuestionResponse,
  WeakPointAnalysisResponse,
  KnowledgePointAnalysis,
  EnhancedTargetPracticeRequest,
  EnhancedTargetPracticeResponse,
  ReviewReminderResponse,
  SpacedRepetitionResponse,
}
