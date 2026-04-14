/**
 * API Types - Aligned with Backend Schemas
 * Generated from backend/app/schemas/*.py
 */

// ========================================
// User Types (from user.py)
// ========================================

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  is_admin: boolean
  created_at: string
  updated_at: string
}

export interface Token {
  access_token: string
  token_type: string
  user: User
}

export interface UserLogin {
  email: string
  password: string
}

export interface UserCreate {
  email: string
  username: string
  password: string
}

// ========================================
// Course Types (from course.py)
// ========================================

export interface CourseBase {
  code: string
  name: string
  description?: string
  difficulty_level: number
  icon?: string
}

export interface CourseSummary extends CourseBase {
  id: number
  is_active: boolean
  chapter_count: number
}

export interface CourseDetail extends CourseBase {
  id: number
  is_active: boolean
  created_at: string
  chapters: ChapterSummary[]
}

export interface CourseListResponse {
  courses: CourseSummary[]
  total: number
}

export interface CourseDetailResponse {
  course: CourseDetail
}

// ========================================
// Chapter Types (from course.py)
// ========================================

export interface ChapterBase {
  title: string
  description?: string
  order_index: number
  learning_objectives?: Record<string, unknown>
  difficulty_tags?: string[]
  skill_tags?: string[]
  estimated_minutes: number
}

export interface ChapterSummary extends ChapterBase {
  id: number
  course_id: number
  is_active: boolean
}

export interface ChapterDetail extends ChapterBase {
  id: number
  course_id: number
  is_active: boolean
  content?: string
}

export interface ChapterDetailResponse {
  chapter: ChapterDetail
  exercises: ExerciseSummary[]
}

// ========================================
// Exercise Types (from exercise.py)
// ========================================

export type ExerciseType = 'choice' | 'programming' | 'fill_blank'

export interface ExerciseBase {
  type: ExerciseType
  difficulty: number
  content: Record<string, unknown>
  hints?: string[]
}

export interface ExerciseSummary extends ExerciseBase {
  id: number
  chapter_id: number
  source: string
}

export interface ExerciseDetail extends ExerciseSummary {
  solution?: Record<string, unknown>
  test_cases?: unknown[]
  common_errors?: string[]
}

export interface ExerciseListResponse {
  exercises: ExerciseSummary[]
  total: number
}

export interface ExerciseGenerateRequest {
  chapter_id: number
  count?: number
  exercise_type?: ExerciseType
  difficulty?: number
  topic?: string
}

export interface ExerciseGenerateResponse {
  success: boolean
  generated: number
  exercises: Record<string, unknown>[]
  message: string
}

export interface ExerciseSubmitRequest {
  answer: unknown
  language?: string
}

export interface ExerciseSubmitResponse {
  is_correct: boolean
  correct_answer?: unknown
  explanation?: string
  xp_earned: number
  points: number
}

// ========================================
// Challenge Types (from challenge.py)
// ========================================

export interface ChallengeBase {
  code: string
  title: string
  description?: string
  icon?: string
  type: string
  difficulty: number
  requirements: Record<string, unknown>
  rewards: Record<string, unknown>
  min_level: number
}

export interface ChallengeSummary extends ChallengeBase {
  id: number
  is_active: boolean
}

export interface ChallengeDetail extends ChallengeBase {
  id: number
  is_active: boolean
  max_attempts: number
  created_at: string
  updated_at: string
}

export interface UserChallengeSummary {
  id: string
  user_id: string
  challenge_id: number
  status: string
  current_progress: number
  target_value: number
  attempts: number
  started_at?: string
  completed_at?: string
}

export interface UserChallengeDetail extends UserChallengeSummary {
  challenge: ChallengeSummary
}

export interface ChallengeListResponse {
  challenges: ChallengeSummary[]
  total: number
}

export interface UserChallengesResponse {
  challenges: UserChallengeDetail[]
  total: number
  completed_count: number
}

// ========================================
// Achievement Types (from achievement.py)
// ========================================

export interface AchievementBase {
  code: string
  title: string
  description?: string
  icon?: string
  type: string
  category: string
  xp_reward: number
  quota_reward: number
  requirements: Record<string, unknown>
  is_secret: boolean
  difficulty: number
}

export interface AchievementSummary extends AchievementBase {
  id: number
  is_active: boolean
  display_order: number
}

export interface AchievementDetail extends AchievementSummary {
  created_at: string
}

export interface AchievementWithEarned extends AchievementSummary {
  earned: boolean
  earned_at?: string
  progress: number
}

export interface UserAchievementSummary {
  id: string
  user_id: string
  achievement_id: number
  earned_at: string
  progress: number
  is_notified: boolean
}

export interface UserAchievementDetail extends UserAchievementSummary {
  achievement: AchievementSummary
}

export interface AchievementListResponse {
  achievements: AchievementSummary[]
  total: number
}

export interface AchievementWithEarnedResponse {
  achievements: AchievementWithEarned[]
  total: number
  earned_count: number
}

export interface UserAchievementsResponse {
  achievements: UserAchievementDetail[]
  total: number
  earned_count: number
}

export interface UserRankResponse {
  rank: number
  user_id: string
  username: string
  level: number
  xp: number
  streak_days: number
  accuracy_rate: number
  total_users: number
}

// ========================================
// Profile Types (from profile.py)
// ========================================

export interface UserProfileResponse {
  id: string
  email: string
  username: string
  xp: number
  level: number
  streak_days: number
  last_activity_date: string
  preferred_languages: string[]
  total_exercises: number
  correct_exercises: number
  accuracy_rate: number
  is_admin: boolean
  ai_quota: number
  created_at: string
}

export interface UpdateProfileRequest {
  preferred_languages?: string[]
}

export interface AddXpRequest {
  xp_amount: number
}

// ========================================
// Checkin Types (from profile.py)
// ========================================

export interface CheckinResponse {
  streak_days: number
  checked_in_today: boolean
  xp_earned: number
  last_checkin_date?: string
}

export interface CheckinStatusResponse {
  streak_days: number
  checked_in_today: boolean
  last_checkin_date?: string
}

// ========================================
// Stats Types (from stats.py)
// ========================================

export interface ChapterProgress {
  id: string
  user_id: string
  chapter_id: number
  status: 'not_started' | 'in_progress' | 'completed'
  progress_percent: number
  completed_subsections: number[]
  completed_exercise_count: number
  completed_exercises_by_subsection: Record<string, number[]>
  exercise_results: Record<string, string>
  started_at?: string
  completed_at?: string
  updated_at: string
}

export interface UpdateProgressRequest {
  status?: string
  progress_percent?: number
  completed_subsections?: number[]
  completed_exercise_count?: number
  total_exercises?: number
  completed_exercises_by_subsection?: Record<string, number[]>
  exercise_results?: Record<string, string>
}

export interface LearningSession {
  id: string
  user_id: string
  chapter_id: number
  subsection_index: number
  started_at: string
  ended_at?: string
  duration_seconds: number
  is_active: boolean
}

export interface StartSessionRequest {
  chapter_id: number
  subsection_index?: number
}

export interface EndSessionRequest {
  duration_seconds: number
}

export interface UpdateSubsectionRequest {
  subsection_index: number
}

export interface LearningStatistics {
  total_learning_time_seconds: number
  total_sessions: number
  completed_chapters: number
  in_progress_chapters: number
  total_subsections_completed: number
  current_streak: number
  longest_streak: number
}

export interface Activity {
  id: string
  activity_type: string
  chapter_id?: number
  subsection_index?: number
  description: string
  extra_data: Record<string, unknown>
  created_at: string
}

// ========================================
// API Response Wrapper
// ========================================

export interface ApiError {
  detail: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}

// ========================================
// AI Types (from ai.py)
// ========================================

export interface ChoiceExplanationRequest {
  question: string
  options: string[]
  user_selected_index: number
  correct_index: number
}

export interface ChoiceExplanationResponse {
  explanation: string
}

export interface CodeReviewRequest {
  code: string
  language: string
  chapter_id?: number
  subsection_index?: number
}

export interface CodeReviewResponse {
  review: string
}

export interface AIChatRequest {
  message: string
}

export interface AIChatResponse {
  reply: string
}

export interface ChoiceAnalysisRequest {
  question_text: string
  options: string[]
  user_selected: string
  correct_answer: string
}

export interface ChoiceAnalysisResponse {
  analysis: string
  correct_explanation: string
  improvement_tips: string[]
}

export interface CodeFeedbackRequest {
  code: string
  language: string
  exercise_description?: string
  expected_output?: string
  actual_output?: string
  status?: string
  error_message?: string
}

export interface CodeFeedbackResponse {
  error_analysis: string
  code_improvement: string
  suggestions: string[]
}

export interface AIConfigResponse {
  provider: string
  model: string
  temperature: number
  is_configured: boolean
  has_api_key: boolean
  api_key_preview?: string
  api_key_length?: number
  connection_status?: string
  connection_address: string
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

export interface AIStatusResponse {
  providers: {
    name: string
    status: 'online' | 'offline' | 'unknown'
    address?: string
    model?: string
    latency_ms?: number
  }[]
}

export interface TestConnectionRequest {
  provider: string
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

// ========================================
// Code Execution Types (from code.py)
// ========================================

export interface CodeExecutionRequest {
  code: string
  language_id: number
  stdin?: string
}

export interface CodeExecutionResponse {
  token: string
  status: string
  status_id: number
  stdout?: string
  stderr?: string
  compile_output?: string
  message?: string
  time?: string
  memory?: string
  exit_code?: number
}

export interface LanguageInfo {
  id: number
  name: string
  monaco_language: string
}

// ========================================
// Trend Types
// ========================================

export interface DailyTrendPoint {
  date: string
  count: number
}

export interface DailyExercisesTrendResponse {
  trends: DailyTrendPoint[]
}

export interface DailyAccuracyTrendPoint {
  date: string
  accuracy: number
  total: number
  correct: number
}

export interface DailyAccuracyTrendResponse {
  trends: DailyAccuracyTrendPoint[]
}

export interface DailyTimeTrendPoint {
  date: string
  minutes: number
}

export interface DailyTimeTrendResponse {
  trends: DailyTimeTrendPoint[]
}

// ========================================
// Favorite Types
// ========================================

export interface FavoriteCreate {
  exercise_id: number
  chapter_id: number
  subsection_index?: number
  note?: string
}

export interface FavoriteResponse {
  id: string
  user_id: string
  exercise_id: number
  chapter_id: number
  subsection_index: number
  note?: string
  created_at: string
}

export interface FavoriteListResponse {
  favorites: FavoriteResponse[]
  total: number
}

export interface FavoriteCountResponse {
  count: number
}

// ========================================
// Note Types
// ========================================

export interface NoteCreate {
  title?: string
  content: string
  exercise_id?: number
  chapter_id?: number
  subsection_index?: number
}

export interface NoteUpdate {
  title?: string
  content?: string
}

export interface NoteResponse {
  id: string
  user_id: string
  title?: string
  content: string
  exercise_id?: number
  chapter_id?: number
  subsection_index: number
  created_at: string
  updated_at: string
}

export interface NoteListResponse {
  notes: NoteResponse[]
  total: number
}

export interface NoteCountResponse {
  count: number
}

// ========================================
// Learning Path Types
// ========================================

export type LearningPathType = 'mastery' | 'challenge'

export type MasteryLevel = '入门' | '学习' | '练习' | '熟练' | '精通'

export type Tier = 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond'

// Mastery Path Types
export interface MasteryOverviewResponse {
  course_id: number
  total_chapters: number
  mastered_chapters: number
  current_chapter: string | null
  current_chapter_id: number | null
  total_mastery_score: number
  avg_mastery: number
  current_mastery_level: MasteryLevel
  completed_chapters: number
  chapters: ChapterMasteryInfo[]
}

export interface ChapterMasteryInfo {
  chapter_id: number
  order_index: number
  title: string
  mastery_score: number
  mastery_level: MasteryLevel
  can_advance: boolean
}

export interface ChapterMasteryResponse {
  chapter_id: number
  chapter_title: string
  mastery_score: number
  mastery_level: MasteryLevel
  accuracy_score: number
  consistency_score: number
  depth_score: number
  recency_score: number
  total_exercises: number
  correct_exercises: number
  can_advance: boolean
  objectives_status: Record<string, unknown> | null
}

// Challenge Path Types
export interface ChallengeStartRequest {
  difficulty_level: number // 1-5
  question_count?: number // 5-20, default 10
}

export interface ChallengeSubmitRequest {
  answers: ChallengeAnswer[]
  total_time: number // seconds
}

export interface ChallengeAnswer {
  exercise_id: string
  answer: string
  is_correct: boolean
  time_spent: number // seconds
}

export interface ChallengeSessionResponse {
  session_id: string
  difficulty_level: number
  exercises: ChallengeExercise[]
  time_limit: number // seconds
  score_multiplier: number
  status: 'pending' | 'in_progress' | 'completed'
}

export interface ChallengeExercise {
  id: number
  title: string
  difficulty: number
  knowledge_points: string[]
}

export interface ChallengeResultResponse {
  session_id: string
  correct_answers: number
  total_questions: number
  base_score: number
  time_bonus: number
  streak_bonus: number
  final_score: number
  tier: Tier
  new_tier: Tier | null
}

// Arena Profile Types
export interface ArenaProfileResponse {
  user_id: string
  course_id: number
  total_score: number
  tier: Tier
  rank: number | null
  total_challenges: number
  wins: number
  losses: number
  highest_difficulty: number
  best_streak: number
  current_streak: number
}

// Leaderboard Types
export interface LeaderboardResponse {
  leaderboard_type: 'mastery' | 'arena'
  course_id: number
  entries: LeaderboardEntry[]
  user_rank: number | null
}

export interface LeaderboardEntry {
  rank: number
  user_id: string
  username: string
  // Mastery leaderboard fields
  total_mastery?: number
  avg_mastery?: number
  chapters_practiced?: number
  mastered_chapters?: number
  total_chapters?: number
  progress_pct?: number
  // Arena leaderboard fields
  total_score?: number
  tier?: Tier
  total_challenges?: number
  wins?: number
  highest_difficulty?: number
}

// Mastery Exercise Recommendation
export interface MasteryExerciseRecommendResponse {
  chapter_id: number
  chapter_title: string
  learning_path: 'mastery'
  exercises: RecommendedExercise[]
}

export interface RecommendedExercise {
  id: number
  title: string
  type: ExerciseType
  difficulty: number
  knowledge_points: string[]
  recommendation_score: number
  reason: string
}
