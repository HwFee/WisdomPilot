/**
 * Review Types - 复习相关类型
 * Aligned with backend/app/schemas/review.py
 */

// ========================================
// Weak Point Types
// ========================================

export interface WeakPointResponse {
  id: string
  user_id: string
  course_id: number
  knowledge_point: string
  error_count: number
  mastery_level: number
  last_error_at?: string
  review_count: number
  last_review_at?: string
}

// ========================================
// Spaced Repetition Types
// ========================================

export interface SpacedRepetitionResponse {
  id: string
  user_id: string
  exercise_id: number
  stage_id?: number
  next_review_at: string
  review_interval: number
  ease_factor: number
  review_count: number
  last_review_at?: string
  last_review_result?: boolean
}

// ========================================
// Review Queue Types
// ========================================

export interface ReviewQueueItem {
  repetition: SpacedRepetitionResponse
  exercise_id: number
  exercise_type: string
  exercise_difficulty: number
  knowledge_points: string[]
  stage_id?: number
  priority: number
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[]
  total_due: number
  total_scheduled: number
}

export interface CompleteReviewRequest {
  exercise_id: number
  quality: number // 0-5
  success: boolean
}

export interface CompleteReviewResponse {
  repetition: SpacedRepetitionResponse
  weak_point_updated: boolean
  mastery_change: number
  message: string
}

export interface TargetPracticeRequest {
  course_id?: number
  knowledge_points?: string[]
  limit: number
}

export interface TargetPracticeResponse {
  exercises: Record<string, unknown>[]
  weak_points: WeakPointResponse[]
  total: number
}

export interface WeakPointListResponse {
  weak_points: WeakPointResponse[]
  total: number
}

export interface ReviewStatsResponse {
  total_due: number
  total_scheduled: number
  reviewed_today: number
  streak_days: number
  weak_points_count: number
  wrong_count?: number
  mastery_distribution: Record<string, number>
}
