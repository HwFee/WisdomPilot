/**
 * Stage Types - 关卡相关类型
 * Aligned with backend/app/schemas/stage.py
 */

// ========================================
// Stage Types
// ========================================

export interface StageBase {
  title: string
  description?: string
  order_index: number
  learning_objectives: string[]
  required_exercises: number
  required_accuracy: number
  verification_questions: number
  xp_reward: number
  quota_bonus: number
  difficulty_level: number
}

export interface StageSummary extends StageBase {
  id: number
  course_id: number
  chapter_id?: number
  is_active: boolean
}

export interface StageDetail extends StageSummary {
  created_at: string
  updated_at: string
}

export interface UserStageProgressResponse {
  id: string
  user_id: string
  stage_id: number
  status: 'locked' | 'unlocked' | 'in_progress' | 'completed'
  exercises_completed: number
  exercises_correct: number
  accuracy: number
  verification_started: boolean
  verification_passed: boolean
  attempts: number
  started_at?: string
  completed_at?: string
}

export interface StageWithProgress extends StageSummary {
  progress?: UserStageProgressResponse
}

export interface StageListResponse {
  stages: StageWithProgress[]
  total: number
}

export interface StageDetailResponse {
  stage: StageDetail
  progress?: UserStageProgressResponse
}

export interface StartStageResponse {
  progress: UserStageProgressResponse
  message: string
}

export interface CompletedExercise {
  exercise_id: number
  exercise_title?: string
  is_correct: boolean
}

export interface CompletePracticeRequest {
  exercises_completed: number
  exercises_correct: number
  completed_exercises?: CompletedExercise[]  // 具体完成的练习题列表
}

export interface CompletePracticeResponse {
  progress: UserStageProgressResponse
  can_start_verification: boolean
  message: string
}

export interface VerificationQuestion {
  id: string
  type: 'choice' | 'programming' | 'fill_blank'
  difficulty: number
  content: {
    text: string
    options?: string[]
  }
  hints?: string[]
}

export interface StartVerificationResponse {
  questions: VerificationQuestion[]
  time_limit: number
  message: string
}

export interface SubmitVerificationRequest {
  answers: Record<string, string | number>
}

export interface SubmitVerificationResponse {
  passed: boolean
  correct_count: number
  total_count: number
  xp_earned: number
  quota_bonus: number
  progress: UserStageProgressResponse
  message: string
}

// ========================================
// Stage Exercise Types
// ========================================

export interface StageExerciseSummary {
  id: number
  type: 'choice' | 'programming' | 'fill_blank'
  difficulty: number
  content: {
    text?: string  // For choice questions
    title?: string  // For programming questions
    options?: string[]
    code_template?: string
    description?: string
    input_format?: string
    output_format?: string
    sample_input?: string
    sample_output?: string
    time_limit?: number
    memory_limit?: number
  }
  hints?: string[]
  knowledge_points: string[]
  test_cases?: Array<{
    input: string
    output: string
    name?: string
  }>
  solution?: {
    answer?: string
    explanation?: string
  }
}

export interface StageExerciseListResponse {
  exercises: StageExerciseSummary[]
  total: number
}

export interface GenerateExercisesRequest {
  count?: number
  exercise_type?: 'choice' | 'programming' | 'fill_blank'
  difficulty?: number
  topic?: string
}

export interface GenerateExercisesResponse {
  success: boolean
  generated: number
  exercises: Array<{
    content: Record<string, unknown>
    solution?: Record<string, unknown>
    hints?: string[]
  }>
  message: string
}
