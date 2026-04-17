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
  // 计算属性
  weakness_score: number
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
  // 计算属性
  is_due: boolean
  days_overdue: number
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

// ========================================
// Wrong Question Types
// ========================================

export interface WrongQuestionResponse {
  id: string
  user_id: string
  exercise_id?: number  // 可选，精进之路/挑战之路错题可能没有
  exercise_key?: string // 精进之路/挑战之路错题的标识
  course_id: number
  chapter_id?: number
  challenge_session_id?: string // 挑战之路会话ID，用于判断来源
  knowledge_points: string[]
  user_answer?: Record<string, unknown> | string  // 可以是对象或字符串
  correct_answer?: Record<string, unknown> | string
  exercise_type: string
  exercise_difficulty: number
  error_count: number
  is_resolved: boolean
  first_error_at: string
  last_error_at: string
  resolved_at?: string
  exercise_content?: Record<string, unknown>
  // 计算属性（后端返回）
  source_type?: string // mastery, arena, enhanced, unknown
  source_label?: string // 精进之路, 挑战之路, 强化测试
  question_title?: string // 题目标题/摘要
}

export interface WrongQuestionListResponse {
  wrong_questions: WrongQuestionResponse[]
  total: number
  unresolved_count: number
}

// ========================================
// Knowledge Point Analysis Types
// ========================================

export interface KnowledgePointAnalysis {
  knowledge_point: string
  error_count: number
  total_attempts: number
  error_rate: number
  mastery_level: number
  weak_score: number
  rank: number
}

export interface WeakPointAnalysisResponse {
  knowledge_points: KnowledgePointAnalysis[]
  weakest_knowledge_points: KnowledgePointAnalysis[]
  strongest_knowledge_points: KnowledgePointAnalysis[]
  total_knowledge_points: number
  overall_error_rate: number
}

// ========================================
// Enhanced Practice Types
// ========================================

export type PracticeMode = 'quick' | 'deep' | 'specific'

export interface EnhancedTargetPracticeRequest {
  course_id?: number
  mode: PracticeMode
  knowledge_points?: string[]
  difficulty_range?: [number, number]
  limit: number
}

export interface EnhancedTargetPracticeResponse {
  exercises: Record<string, unknown>[]
  weak_points: WeakPointResponse[]
  mode: PracticeMode
  total: number
  message: string
}

// ========================================
// Review Reminder Types
// ========================================

export interface ReviewReminderResponse {
  due_reviews: ReviewQueueItem[]
  upcoming_reviews: { date: string; count: number; label: string }[]
  ebbinghaus_schedule: { day: number; label: string; count: number }[]
  total_due: number
  total_upcoming: number
}
