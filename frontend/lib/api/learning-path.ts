/**
 * Learning Path API - Dual learning path system endpoints
 *
 * Mastery Path (精进之路): Chapter-based learning for beginners
 * Challenge Path (挑战之路): Difficulty-based challenges for competitive learners
 */

import { get, post } from './client'
import type {
  MasteryOverviewResponse,
  ChapterMasteryResponse,
  MasteryExerciseRecommendResponse,
  ArenaProfileResponse,
  ChallengeStartRequest,
  ChallengeSessionResponse,
  ChallengeSubmitRequest,
  ChallengeResultResponse,
  LeaderboardResponse,
  KnowledgeContentResponse,
  MasteryQuizGenerateRequest,
  MasteryQuizGenerateResponse,
  MasteryQuizSubmitRequest,
  MasteryQuizSubmitResponse,
  // New base question types
  BaseQuestionListResponse,
  BaseAnswersSubmitRequest,
  BaseAnswersSubmitResponse,
  EnhancedQuizGenerateRequest,
  EnhancedQuizGenerateResponse,
  EnhancedQuizSubmitRequest,
  EnhancedQuizSubmitResponse,
} from '@/types/api'

// ========================================
// Mastery Path APIs
// ========================================

/**
 * Get user's mastery path overview for a course
 */
export async function getMasteryOverview(
  courseId: number,
  token: string
): Promise<MasteryOverviewResponse> {
  return get<MasteryOverviewResponse>(`/api/learning-path/mastery/${courseId}/overview`, token)
}

/**
 * Get detailed mastery info for a specific chapter
 */
export async function getChapterMastery(
  courseId: number,
  chapterId: number,
  token: string
): Promise<ChapterMasteryResponse> {
  return get<ChapterMasteryResponse>(
    `/api/learning-path/mastery/${courseId}/chapter/${chapterId}`,
    token
  )
}

/**
 * Get recommended exercises for mastery path (chapter-based)
 */
export async function getMasteryExerciseRecommendations(
  courseId: number,
  chapterId: number,
  token: string,
  limit: number = 5
): Promise<MasteryExerciseRecommendResponse> {
  return get<MasteryExerciseRecommendResponse>(
    `/api/learning-path/mastery/${courseId}/chapter/${chapterId}/recommend?limit=${limit}`,
    token
  )
}

// ========================================
// Challenge Path APIs
// ========================================

/**
 * Get user's arena profile for a course
 */
export async function getArenaProfile(
  courseId: number,
  token: string
): Promise<ArenaProfileResponse> {
  return get<ArenaProfileResponse>(`/api/learning-path/challenge/${courseId}/profile`, token)
}

/**
 * Start a new challenge session
 */
export async function startChallengeSession(
  courseId: number,
  request: ChallengeStartRequest,
  token: string
): Promise<ChallengeSessionResponse> {
  return post<ChallengeSessionResponse>(
    `/api/learning-path/challenge/${courseId}/start`,
    token,
    request
  )
}

/**
 * Submit challenge answers and get results
 */
export async function submitChallengeSession(
  courseId: number,
  sessionId: string,
  request: ChallengeSubmitRequest,
  token: string
): Promise<ChallengeResultResponse> {
  return post<ChallengeResultResponse>(
    `/api/learning-path/challenge/${courseId}/session/${sessionId}/submit`,
    token,
    request
  )
}

// ========================================
// Leaderboard APIs
// ========================================

/**
 * Get mastery leaderboard for a course (精进榜)
 */
export async function getMasteryLeaderboard(
  courseId: number,
  token: string,
  limit: number = 50,
  offset: number = 0
): Promise<LeaderboardResponse> {
  return get<LeaderboardResponse>(
    `/api/learning-path/leaderboard/${courseId}/mastery?limit=${limit}&offset=${offset}`,
    token
  )
}

/**
 * Get arena leaderboard for a course (竞技榜)
 */
export async function getArenaLeaderboard(
  courseId: number,
  token: string,
  limit: number = 50,
  offset: number = 0
): Promise<LeaderboardResponse> {
  return get<LeaderboardResponse>(
    `/api/learning-path/leaderboard/${courseId}/arena?limit=${limit}&offset=${offset}`,
    token
  )
}

// ========================================
// Tier Utilities
// ========================================

export const TIER_THRESHOLDS: Record<string, number> = {
  bronze: 0,
  silver: 1000,
  gold: 2500,
  platinum: 5000,
  diamond: 10000,
}

export const TIER_ICONS: Record<string, string> = {
  bronze: '🥉',
  silver: '🥈',
  gold: '🥇',
  platinum: '💎',
  diamond: '👑',
}

export const TIER_NAMES: Record<string, string> = {
  bronze: '青铜',
  silver: '白银',
  gold: '黄金',
  platinum: '铂金',
  diamond: '钻石',
}

export const MASTERY_LEVEL_COLORS: Record<string, string> = {
  '入门': 'text-gray-500',
  '学习': 'text-blue-500',
  '练习': 'text-green-500',
  '熟练': 'text-yellow-500',
  '精通': 'text-purple-500',
}

// ========================================
// Mastery Quiz APIs (精进之路测试)
// ========================================

/**
 * Get chapter knowledge content for mastery path
 */
export async function getChapterKnowledgeContent(
  courseId: number,
  chapterId: number,
  token: string
): Promise<KnowledgeContentResponse> {
  return get<KnowledgeContentResponse>(
    `/api/learning-path/mastery/${courseId}/chapter/${chapterId}/knowledge`,
    token
  )
}

/**
 * Generate mastery quiz questions based on user profile
 */
export async function generateMasteryQuiz(
  courseId: number,
  request: MasteryQuizGenerateRequest,
  token: string
): Promise<MasteryQuizGenerateResponse> {
  return post<MasteryQuizGenerateResponse>(
    `/api/learning-path/mastery/${courseId}/generate-quiz`,
    token,
    request
  )
}

/**
 * Submit mastery quiz answers and get results
 */
export async function submitMasteryQuiz(
  courseId: number,
  request: MasteryQuizSubmitRequest,
  token: string
): Promise<MasteryQuizSubmitResponse> {
  return post<MasteryQuizSubmitResponse>(
    `/api/learning-path/mastery/${courseId}/submit-quiz`,
    token,
    request
  )
}

// ========================================
// Chapter Base Question APIs (章节基础测试题)
// ========================================

/**
 * Get chapter base questions (fixed questions from database)
 */
export async function getChapterBaseQuestions(
  courseId: number,
  chapterId: number,
  token: string
): Promise<BaseQuestionListResponse> {
  return get<BaseQuestionListResponse>(
    `/api/learning-path/mastery/${courseId}/chapter/${chapterId}/base-questions`,
    token
  )
}

/**
 * Submit base question answers and get weak/strong point analysis
 */
export async function submitBaseAnswers(
  courseId: number,
  chapterId: number,
  request: BaseAnswersSubmitRequest,
  token: string
): Promise<BaseAnswersSubmitResponse> {
  return post<BaseAnswersSubmitResponse>(
    `/api/learning-path/mastery/${courseId}/chapter/${chapterId}/submit-base`,
    token,
    request
  )
}

/**
 * Generate enhanced quiz based on weak points
 */
export async function generateEnhancedQuiz(
  courseId: number,
  request: EnhancedQuizGenerateRequest,
  token: string
): Promise<EnhancedQuizGenerateResponse> {
  return post<EnhancedQuizGenerateResponse>(
    `/api/learning-path/mastery/${courseId}/generate-enhanced`,
    token,
    request
  )
}

/**
 * Submit enhanced quiz answers
 */
export async function submitEnhancedQuiz(
  courseId: number,
  request: EnhancedQuizSubmitRequest,
  token: string
): Promise<EnhancedQuizSubmitResponse> {
  return post<EnhancedQuizSubmitResponse>(
    `/api/learning-path/mastery/${courseId}/submit-enhanced`,
    token,
    request
  )
}

// ========================================
// Arena Infinite Mode APIs
// ========================================

export interface InfiniteSessionStartRequest {
  difficulty_level?: number
  initial_count?: number
}

export interface InfiniteProgressResponse {
  session_id: string
  current_index: number
  total_exercises: number
  exercises: Array<{
    exercise_id: number
    exercise_index: number
    is_completed: boolean
    is_correct: boolean
    is_unlocked: boolean
    saved_code: string
    current_language: string
    title: string
    difficulty: number
  }>
  correct_count: number
  completed_count: number
  total_xp_earned: number
}

export interface SubmitExerciseRequest {
  exercise_id: number
  code: string
  language: string
  test_results: Array<{ passed: boolean; input: string; expected: string; actual: string }>
}

export interface SubmitExerciseResponse {
  is_correct: boolean
  test_results: Array<{ passed: boolean; input: string; expected: string; actual: string }>
  xp_earned: number
  next_unlocked: boolean
  added_to_wrong_book: boolean
}

export interface SaveCodeRequest {
  exercise_id: number
  code: string
  language: string
}

export interface SwitchExerciseRequest {
  target_index: number
}

export interface SwitchExerciseResponse {
  exercise_id: number
  saved_code: string
  current_language: string
  is_completed: boolean
  is_correct: boolean
  exercise: ChallengeExercise
}

export interface AppendExercisesRequest {
  count?: number
}

export interface AppendExercisesResponse {
  new_exercise_ids: number[]
  count: number
}

export interface ExitSaveRequest {
  current_exercise_id: number
  current_code: string
  current_language: string
}

export interface ChallengeExercise {
  id: number
  title: string
  type: string
  difficulty: number
  knowledge_points: string[]
  content: {
    text?: string
    title?: string
    options?: string[]
    code_template?: string
    description?: string
    samples?: Array<{ input: string; output: string }>
  }
  test_cases?: Array<{ input: string; output: string }> | null
}

/**
 * Start infinite mode session
 */
export async function startInfiniteSession(
  courseId: number,
  request: InfiniteSessionStartRequest,
  token: string
): Promise<ChallengeSessionResponse> {
  return post<ChallengeSessionResponse>(
    `/api/learning-path/challenge/${courseId}/infinite/start`,
    token,
    request
  )
}

/**
 * Get challenge path progress (no session_id needed)
 */
export async function getChallengeProgress(
  courseId: number,
  token: string
): Promise<InfiniteProgressResponse> {
  return get<InfiniteProgressResponse>(
    `/api/learning-path/challenge/${courseId}/progress`,
    token
  )
}

/**
 * Submit exercise answer in challenge path
 */
export async function submitChallengeExercise(
  courseId: number,
  request: SubmitExerciseRequest,
  token: string
): Promise<SubmitExerciseResponse> {
  return post<SubmitExerciseResponse>(
    `/api/learning-path/challenge/${courseId}/submit`,
    token,
    request
  )
}

/**
 * Save code for an exercise
 */
export async function saveChallengeCode(
  courseId: number,
  request: SaveCodeRequest,
  token: string
): Promise<{ success: boolean }> {
  return post<{ success: boolean }>(
    `/api/learning-path/challenge/${courseId}/save-code`,
    token,
    request
  )
}

/**
 * Switch to a different exercise by index
 */
export async function switchChallengeExercise(
  courseId: number,
  request: SwitchExerciseRequest,
  token: string
): Promise<SwitchExerciseResponse> {
  return post<SwitchExerciseResponse>(
    `/api/learning-path/challenge/${courseId}/switch`,
    token,
    request
  )
}

/**
 * Append more exercises to challenge path
 */
export async function appendChallengeExercises(
  courseId: number,
  request: AppendExercisesRequest,
  token: string
): Promise<AppendExercisesResponse> {
  return post<AppendExercisesResponse>(
    `/api/learning-path/challenge/${courseId}/append`,
    token,
    request
  )
}

/**
 * Get specific exercise info (for wrong question book / favorites)
 */
export async function getChallengeExercise(
  courseId: number,
  exerciseId: number,
  token: string
): Promise<{
  exercise: ChallengeExercise
  exercise_index: number
  is_unlocked: boolean
  is_completed: boolean
  is_correct: boolean
  saved_code: string
  current_language: string
  total_exercises: number
}> {
  return get(
    `/api/learning-path/challenge/${courseId}/exercise/${exerciseId}`,
    token
  )
}

// ========================================
// Legacy APIs (for backward compatibility)
// ========================================

/**
 * Get infinite mode progress (legacy - use getChallengeProgress)
 */
export async function getInfiniteProgress(
  courseId: number,
  sessionId: string,
  token: string
): Promise<InfiniteProgressResponse> {
  return get<InfiniteProgressResponse>(
    `/api/learning-path/challenge/${courseId}/infinite/${sessionId}/progress`,
    token
  )
}

/**
 * Submit exercise answer in infinite mode (legacy - use submitChallengeExercise)
 */
export async function submitInfiniteExercise(
  courseId: number,
  sessionId: string,
  request: SubmitExerciseRequest,
  token: string
): Promise<SubmitExerciseResponse> {
  return post<SubmitExerciseResponse>(
    `/api/learning-path/challenge/${courseId}/infinite/${sessionId}/submit`,
    token,
    request
  )
}

/**
 * Save code for an exercise (legacy - use saveChallengeCode)
 */
export async function saveInfiniteCode(
  courseId: number,
  sessionId: string,
  request: SaveCodeRequest,
  token: string
): Promise<{ success: boolean }> {
  return post<{ success: boolean }>(
    `/api/learning-path/challenge/${courseId}/infinite/${sessionId}/save-code`,
    token,
    request
  )
}

/**
 * Switch to a different exercise (legacy - use switchChallengeExercise)
 */
export async function switchInfiniteExercise(
  courseId: number,
  sessionId: string,
  request: SwitchExerciseRequest,
  token: string
): Promise<SwitchExerciseResponse> {
  return post<SwitchExerciseResponse>(
    `/api/learning-path/challenge/${courseId}/infinite/${sessionId}/switch`,
    token,
    request
  )
}

/**
 * Append more exercises to session (legacy - use appendChallengeExercises)
 */
export async function appendInfiniteExercises(
  courseId: number,
  sessionId: string,
  request: AppendExercisesRequest,
  token: string
): Promise<AppendExercisesResponse> {
  return post<AppendExercisesResponse>(
    `/api/learning-path/challenge/${courseId}/infinite/${sessionId}/append`,
    token,
    request
  )
}

/**
 * Save progress and exit infinite mode
 */
export async function exitInfiniteSession(
  courseId: number,
  sessionId: string,
  request: ExitSaveRequest,
  token: string
): Promise<{ success: boolean; message: string }> {
  return post<{ success: boolean; message: string }>(
    `/api/learning-path/challenge/${courseId}/infinite/${sessionId}/exit`,
    token,
    request
  )
}

/**
 * 获取用户某门课的活跃挑战会话（用于错题本跳转）
 */
export async function getActiveChallengeSession(
  courseId: number,
  token: string
): Promise<{
  session: {
    id: string
    course_id: number
    status: string
    current_index: number
    total_exercises: number
    exercise_ids: number[]
  } | null
  exercise_map: Record<number, {
    exercise_index: number
    is_completed: boolean
    is_correct: boolean
    is_unlocked: boolean
  }>
  message?: string
}> {
  return get<{
    session: {
      id: string
      course_id: number
      status: string
      current_index: number
      total_exercises: number
      exercise_ids: number[]
    } | null
    exercise_map: Record<number, {
      exercise_index: number
      is_completed: boolean
      is_correct: boolean
      is_unlocked: boolean
    }>
    message?: string
  }>(
    `/api/learning-path/challenge/${courseId}/active-session`,
    token
  )
}

// ========================================
// Mastery Progress APIs (精进之路进度)
// ========================================

export interface SaveMasteryExerciseProgressRequest {
  course_id: number
  chapter_id: number
  question_id: number
  question_type?: 'base' | 'enhanced'
  exercise_key?: string
  is_completed: boolean
  is_correct: boolean
  user_answer?: string
  correct_answer?: string
  attempt_count?: number
}

export interface SaveMasteryExerciseProgressResponse {
  success: boolean
  progress_id?: string
  message: string
}

export interface MasteryChapterProgressResponse {
  chapter_id: number
  total_questions: number
  completed_questions: number
  correct_questions: number
  mastery_score: number
  is_passed: boolean
}

export interface MasteryQuizCompleteRequest {
  course_id: number
  chapter_id: number
  results: Array<{
    question_id: number
    is_correct: boolean
    user_answer: string
    correct_answer: string
  }>
}

export interface MasteryProgressByKeyResponse {
  found: boolean
  progress?: {
    course_id: number
    chapter_id: number
    question_id: number
    question_index: number
    is_completed: boolean
    is_correct: boolean
  }
  message?: string
}

/**
 * 保存精进之路做题进度
 */
export async function saveMasteryExerciseProgress(
  request: SaveMasteryExerciseProgressRequest,
  token: string
): Promise<SaveMasteryExerciseProgressResponse> {
  return post<SaveMasteryExerciseProgressResponse>(
    '/api/learning-path/mastery/progress/exercise',
    token,
    request
  )
}

/**
 * 获取精进之路章节进度
 */
export async function getMasteryChapterProgress(
  courseId: number,
  chapterId: number,
  token: string
): Promise<MasteryChapterProgressResponse> {
  return get<MasteryChapterProgressResponse>(
    `/api/learning-path/mastery/${courseId}/${chapterId}/progress`,
    token
  )
}

/**
 * 完成章节quiz时更新ChapterMastery
 */
export async function completeMasteryQuiz(
  request: MasteryQuizCompleteRequest,
  token: string
): Promise<{ success: boolean; message: string }> {
  return post<{ success: boolean; message: string }>(
    '/api/learning-path/mastery/progress/complete-quiz',
    token,
    request
  )
}

/**
 * 根据exercise_key获取做题进度（用于错题本跳转定位）
 */
export async function getMasteryProgressByKey(
  exerciseKey: string,
  token: string
): Promise<MasteryProgressByKeyResponse> {
  return get<MasteryProgressByKeyResponse>(
    `/api/learning-path/mastery/progress/exercise/${exerciseKey}`,
    token
  )
}

// ========================================
// Mastery Chapter Detail Progress APIs
// ========================================

export interface MasteryExerciseProgressItem {
  question_id: number
  question_index: number
  question_type: string
  is_completed: boolean
  is_correct: boolean
  user_answer?: string
  correct_answer?: string
  saved_code?: string
  current_language: string
  attempt_count: number
}

export interface MasteryChapterDetailProgressResponse {
  chapter_id: number
  total_questions: number
  completed_questions: number
  correct_questions: number
  mastery_score: number
  is_passed: boolean
  progress_items: MasteryExerciseProgressItem[]
}

/**
 * 获取精进之路章节详细进度 - 包含每道题的进度信息
 */
export async function getMasteryChapterDetailProgress(
  courseId: number,
  chapterId: number,
  token: string
): Promise<MasteryChapterDetailProgressResponse> {
  return get<MasteryChapterDetailProgressResponse>(
    `/api/learning-path/mastery/${courseId}/${chapterId}/progress/detail`,
    token
  )
}
