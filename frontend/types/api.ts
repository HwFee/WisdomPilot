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
  username: string
  password: string
  remember_me?: boolean
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
  course_id?: number
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
  total_checkin_days: number
  last_activity_date: string
  preferred_languages: string[]
  total_exercises: number
  correct_exercises: number
  accuracy_rate: number
  is_admin: boolean
  cores: number
  cores_total_earned: number
  cores_total_spent: number
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
  cores_earned: number
  last_checkin_date?: string
  total_checkin_days: number
  streak_multiplier: number
  new_achievements: string[]
}

export interface CheckinStatusResponse {
  streak_days: number
  checked_in_today: boolean
  last_checkin_date?: string
  total_checkin_days: number
}

export interface CheckinDetailsResponse {
  date: string
  lunar_str: string
  solar_term_str: string
  holiday_str: string
  streak_days: number
  total_checkin_days: number
  streak_multiplier: number
  checked_in_today: boolean
}

export interface CheckinStatsResponse {
  streak_days: number
  total_checkin_days: number
  streak_multiplier: number
  checked_in_today: boolean
  next_tier_days: number | null
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
// Trend Types (from stats.py)
// ========================================

export interface DailyTrendPoint {
  date: string // ISO date string YYYY-MM-DD
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
// Favorite Types - 与错题本完全一致
// ========================================

export interface FavoriteCreate {
  // 与错题本 CollectWrongQuestionRequest 一致
  exercise_key: string  // 格式: mastery-{courseId}-{chapterId}-{exerciseId} 或 arena-{courseId}-{exerciseId} 或 enhanced-{courseId}-{sectionId}-{exerciseId}
  course_id: number
  chapter_id?: number
  section_id?: number
  exercise_id?: number
  exercise_content?: {
    title?: string
    text?: string
    description?: string
    options?: string[]
  }
  exercise_type?: string
  exercise_difficulty?: number
  knowledge_points?: string[]
  // 收藏夹特有
  folder?: string
  note?: string
}

export interface FavoriteUpdate {
  folder?: string
  note?: string
}

export interface FavoriteResponse {
  // 与错题本 WrongQuestionResponse 一致
  id: string
  user_id: string
  exercise_id?: number
  exercise_key?: string
  course_id: number
  chapter_id?: number
  section_id?: number
  knowledge_points: string[]
  exercise_content?: {
    title?: string
    text?: string
    description?: string
    options?: string[]
  }
  exercise_type: string
  exercise_difficulty: number
  // source_type/source_label/question_title 通过 exercise_key 推断（前端计算或后端 property）
  // 收藏夹特有
  folder?: string
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

export interface FavoriteFolderResponse {
  name: string
  count: number
}

export interface FavoriteFoldersListResponse {
  folders: FavoriteFolderResponse[]
}

// ========================================
// Note Types
// ========================================

export interface NoteCreate {
  title?: string
  content: string
  course_id?: number
  chapter_id?: number
  section_id?: number
  exercise_id?: number
  subsection_index?: number
  tags?: string[]
  knowledge_points?: string[]
  source?: 'manual' | 'ai_answer' | 'question'
}

export interface NoteUpdate {
  title?: string
  content?: string
  tags?: string[]
  knowledge_points?: string[]
}

export interface NoteFromQuestion {
  title?: string
  content: string
  course_id?: number
  chapter_id?: number
  section_id?: number
  exercise_id?: number
  subsection_index?: number
  knowledge_points?: string[]
  source: 'ai_answer' | 'question'
  question_content?: string
  ai_answer_content?: string
}

export interface NoteResponse {
  id: string
  user_id: string
  title?: string
  content: string
  course_id?: number
  chapter_id?: number
  section_id?: number
  exercise_id?: number
  subsection_index: number
  tags: string[]
  knowledge_points: string[]
  source: 'manual' | 'ai_answer' | 'question'
  processing_status: 'pending' | 'processing' | 'completed'
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

export interface NoteSearchResponse {
  notes: NoteResponse[]
  total: number
  query: string
}

export interface NoteExportRequest {
  note_ids: string[]
  format: 'markdown' | 'json'
}

// ========================================
// Note Tag Types
// ========================================

export interface NoteTagCreate {
  name: string
  color?: string
}

export interface NoteTagUpdate {
  name?: string
  color?: string
}

export interface NoteTagResponse {
  id: string
  user_id: string
  name: string
  color: string
  created_at: string
}

export interface NoteTagListResponse {
  tags: NoteTagResponse[]
  total: number
}

// ========================================
// Learning Path Types
// ========================================

export type LearningPathType = 'mastery' | 'challenge'

export type MasteryLevel = '入门' | '学习' | '练习' | '熟练' | '精通'

// 王者荣耀风格段位系统
export type TierRank = 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond' | 'master' | 'king'

// 段位配置
export interface TierConfig {
  rank: TierRank
  name: string           // 中文名称
  sub_tiers: number      // 小段位数量
  stars_per_tier: number // 每小段位星星数
  color: string          // 颜色
  icon: string           // 图标
  protection_count: number // 保护次数
}

// 段位信息
export interface TierInfo {
  tier: TierRank
  tier_name: string
  sub_tier: number       // 小段位 (1=I, 2=II, 3=III, 4=IV, 5=V)
  sub_tier_name: string  // 罗马数字
  full_name: string      // 完整名称如"黄金III"
  stars: number          // 当前星星数
  stars_needed: number   // 升级所需星星
  protection_remaining: number // 剩余保护次数
  color: string
  icon: string
  highest_tier?: TierRank
  highest_sub_tier?: number
  highest_full_name?: string
}

// 更新星星结果
export interface UpdateStarsResult {
  tier: TierRank
  sub_tier: number
  stars: number
  stars_change: number
  promoted: boolean
  demoted: boolean
  used_protection: boolean
  protection_remaining: number
  full_name: string
  message: string
}

// 兼容旧版Tier类型
export type Tier = TierRank

// Mastery Path Types
export interface MasteryOverviewResponse {
  course_id: number
  total_chapters: number
  mastered_chapters: number
  current_chapter: number | null
  total_mastery_points: number
  avg_mastery: number
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
  z_id?: string
  title: string
  type: ExerciseType
  difficulty: number
  knowledge_points: string[]
  content: {
    text: string
    title?: string
    options?: string[]
    code_template?: string
    description?: string
    samples?: Array<{ input: string; output: string }>
  }
  test_cases?: Array<{ input: string; output: string }> | null
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
  mastery_xp?: number  // 精进经验值（主要排序依据）
  mastery_level?: number
  total_mastery?: number
  avg_mastery?: number
  chapters_practiced?: number
  mastered_chapters?: number
  total_chapters?: number
  progress_pct?: number
  // Arena leaderboard fields
  total_score?: number  // Keep for backward compatibility
  stars?: number  // New: stars count
  tier?: Tier
  sub_tier?: number  // New: sub-tier (I, II, III, IV, V)
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

// ========================================
// Mastery Quiz Types (精进之路测试)
// ========================================

export interface KnowledgePoint {
  id: string
  title: string
  content: string
  examples: string[]
  difficulty: number
  related_points?: string[]
}

export interface KnowledgeContentResponse {
  chapter_id: number
  chapter_title: string
  knowledge_points: KnowledgePoint[]
  total_points: number
  estimated_time: number
  prerequisites: string[] | null
  next_chapters: number[] | null
}

export interface MasteryQuizQuestion {
  id: string
  type: 'choice' | 'programming' | 'fill_blank'
  difficulty: number
  content: {
    text: string
    options?: string[]
    code_template?: string
    test_cases?: Array<{ input: string; expected: string }>
  }
  solution: {
    answer: string
    explanation?: string
  }
  knowledge_points: string[]
}

export interface MasteryQuizGenerateRequest {
  course_id: number
  chapter_id: number
  question_count?: number
  question_types?: string[]
  difficulty_range?: [number, number]
  focus_weak_points?: boolean
}

export interface MasteryQuizGenerateResponse {
  success: boolean
  session_id: string
  questions: MasteryQuizQuestion[]
  user_profile_used: boolean
  weak_points_addressed: string[]
  message: string
}

export interface QuizAnswer {
  question_id: string
  answer: string
  time_spent?: number
}

export interface MasteryQuizSubmitRequest {
  session_id: string
  answers: QuizAnswer[]
  total_time?: number
}

export interface QuestionResult {
  question_id: string
  is_correct: boolean
  user_answer: string
  correct_answer: string
  explanation?: string
  knowledge_points: string[]
}

export interface MasteryQuizSubmitResponse {
  success: boolean
  session_id: string
  total_questions: number
  correct_answers: number
  accuracy: number
  xp_earned: number
  mastery_points_earned: number
  results: QuestionResult[]
  recommendations: string[]
  passed: boolean
  message: string
}

// ========================================
// Section Base Question Types (小节基础测试题)
// ========================================

export interface BaseQuestionResponse {
  id: number
  section_id: number
  chapter_id?: number
  order_index: number
  type: 'choice' | 'programming' | 'fill_blank'
  title?: string
  text: string
  options?: string[]
  correct_answer?: string
  explanation?: string
  knowledge_points: string[]
  difficulty: number
  code_template?: string
  test_cases?: Array<{ input: string; expected: string }>
  // Alias for type field (backend returns 'type', but we also support 'question_type')
  question_type?: 'choice' | 'programming' | 'fill_blank'
}

export interface BaseQuestionListResponse {
  section_id: number
  section_title: string
  chapter_id: number
  total_questions: number
  questions: BaseQuestionResponse[]
}

export interface BaseAnswerSubmit {
  question_id: number
  answer: string
  time_spent?: number
}

export interface BaseAnswersSubmitRequest {
  section_id: number
  answers: BaseAnswerSubmit[]
}

export interface BaseQuestionResult {
  question_id: number
  is_correct: boolean
  user_answer: string
  correct_answer: string
  explanation?: string
  knowledge_points: string[]
}

export interface BaseAnswersSubmitResponse {
  section_id: number
  total_questions: number
  correct_answers: number
  accuracy: number
  results: BaseQuestionResult[]
  weak_points: string[]
  strong_points: string[]
  xp_earned: number
}

export interface EnhancedQuizGenerateRequest {
  course_id: number
  section_id: number
  chapter_id: number
  weak_points?: string[]
  strong_points?: string[]
  question_count?: number
  question_types?: string[]
}

export interface EnhancedQuizQuestion {
  id: string
  type: 'choice' | 'programming' | 'fill_blank'
  difficulty: number
  text: string
  options?: string[]
  correct_answer: string // 正确答案
  explanation?: string // 答案解析
  code_template?: string
  test_cases?: Array<{ input: string; expected: string }>
  knowledge_points: string[]
}

export interface EnhancedQuizGenerateResponse {
  success: boolean
  session_id: string
  questions: EnhancedQuizQuestion[]
  weak_points_addressed: string[]
  message: string
}

export interface EnhancedQuizSubmitRequest {
  session_id: string
  section_id: number
  answers: Array<{ question_id: string; answer: string }>
}

export interface EnhancedQuizSubmitResponse {
  success: boolean
  session_id: string
  section_id: number
  total_questions: number
  correct_answers: number
  accuracy: number
  xp_earned: number
  mastery_points_earned: number
  results: Array<{
    question_id: string
    is_correct: boolean
    user_answer: string
    correct_answer: string
    explanation?: string
    knowledge_points: string[]
  }>
  recommendations: string[]
  passed: boolean
  message: string
}
