/**
 * Review API - 复习系统接口
 */

import {
  ReviewQueueResponse,
  CompleteReviewRequest,
  CompleteReviewResponse,
  TargetPracticeRequest,
  TargetPracticeResponse,
  WeakPointListResponse,
  ReviewStatsResponse,
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
  token: string
): Promise<WeakPointListResponse> {
  return get<WeakPointListResponse>('/api/review/weak-points', token)
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

// Re-export types
export type {
  ReviewQueueResponse,
  CompleteReviewResponse,
  TargetPracticeResponse,
  WeakPointListResponse,
  ReviewStatsResponse,
}
