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

// Re-export types for external use
export type { MasteryOverviewResponse }

type LegacyMasteryOverviewResponse = MasteryOverviewResponse & {
  total_mastery_score?: number
}

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
  const data = await get<LegacyMasteryOverviewResponse>(`/api/learning-path/mastery/${courseId}/overview`, token)

  return {
    ...data,
    current_chapter: typeof data.current_chapter === 'number' ? data.current_chapter : null,
    total_mastery_points: data.total_mastery_points ?? data.total_mastery_score ?? 0,
  }
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

// 段位名称映射（用于文本显示）
export const TIER_NAMES: Record<string, string> = {
  bronze: '青铜',
  silver: '白银',
  gold: '黄金',
  platinum: '铂金',
  diamond: '钻石',
  master: '星耀',
  king: '王者',
}

// 注意：段位图标现在从 @/lib/icons/tier-icons 导入 React 组件
// 使用 getTierConfig(tier).icon 获取图标组件

export const MASTERY_LEVEL_COLORS: Record<string, string> = {
  '入门': 'text-gray-500',
  '学习': 'text-blue-500',
  '练习': 'text-green-500',
  '熟练': 'text-yellow-500',
  '精通': 'text-purple-500',
}

// 注意：掌握等级图标现在从 @/lib/icons/course-icons 导入 React 组件
// 使用 MASTERY_LEVEL_ICONS[level] 获取图标组件

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
 * Get section base questions (fixed questions from database)
 */
export async function getSectionBaseQuestions(
  sectionId: number,
  token: string
): Promise<BaseQuestionListResponse> {
  return get<BaseQuestionListResponse>(
    `/api/learning-path/mastery/section/${sectionId}/base-questions`,
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
 * Note: Uses longer timeout (120s) because AI generation takes time
 */
export async function generateEnhancedQuiz(
  courseId: number,
  request: EnhancedQuizGenerateRequest,
  token: string
): Promise<EnhancedQuizGenerateResponse> {
  // AI 生成题目需要较长时间，使用 120 秒超时
  return post<EnhancedQuizGenerateResponse>(
    `/api/learning-path/mastery/${courseId}/generate-enhanced`,
    token,
    request,
    120000  // 120 seconds
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
  total_stars_earned: number
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
  stars_earned: number
  cores_earned: number
  next_unlocked: boolean
  added_to_wrong_book: boolean
  tier_changed: boolean
  new_tier: string | null
  new_sub_tier: number | null
  new_stars: number
  promoted: boolean
  demoted: boolean
  first_time_correct: boolean
  first_time_wrong: boolean
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
  difficulty_level?: number
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
 * Start infinite mode session (challenge path - independent of courses)
 */
export async function startInfiniteSession(
  request: InfiniteSessionStartRequest,
  token: string
): Promise<ChallengeSessionResponse> {
  return post<ChallengeSessionResponse>(
    `/api/learning-path/challenge/infinite/start`,
    token,
    request
  )
}

/**
 * Get challenge path progress (no session_id needed, independent of courses)
 * lite=True (default): Returns metadata only, much faster for large exercise lists
 * lite=False: Returns full content and test_cases for all exercises
 */
export async function getChallengeProgress(
  token: string,
  lite: boolean = true
): Promise<InfiniteProgressResponse> {
  return get<InfiniteProgressResponse>(
    `/api/learning-path/challenge/progress?lite=${lite}`,
    token
  )
}

/**
 * Get full content for a single exercise (used with lite mode)
 * Fetches complete exercise data on demand when user views an exercise
 */
export async function getChallengeExerciseContent(
  exerciseId: number,
  token: string
): Promise<{ exercise: ChallengeExercise; exercise_index: number; is_unlocked: boolean; is_completed: boolean; is_correct: boolean; saved_code: string; current_language: string; total_exercises: number }> {
  return get(
    `/api/learning-path/challenge/exercise/${exerciseId}`,
    token
  )
}

/**
 * Submit exercise answer in challenge path (independent of courses)
 */
export async function submitChallengeExercise(
  request: SubmitExerciseRequest,
  token: string
): Promise<SubmitExerciseResponse> {
  return post<SubmitExerciseResponse>(
    `/api/learning-path/challenge/submit`,
    token,
    request
  )
}

/**
 * Save code for an exercise (independent of courses)
 */
export async function saveChallengeCode(
  request: SaveCodeRequest,
  token: string
): Promise<{ success: boolean }> {
  return post<{ success: boolean }>(
    `/api/learning-path/challenge/save-code`,
    token,
    request
  )
}

/**
 * Switch to a different exercise by index (independent of courses)
 */
export async function switchChallengeExercise(
  request: SwitchExerciseRequest,
  token: string
): Promise<SwitchExerciseResponse> {
  return post<SwitchExerciseResponse>(
    `/api/learning-path/challenge/switch`,
    token,
    request
  )
}

/**
 * Append more exercises to challenge path (independent of courses)
 */
export async function appendChallengeExercises(
  request: AppendExercisesRequest,
  token: string
): Promise<AppendExercisesResponse> {
  return post<AppendExercisesResponse>(
    `/api/learning-path/challenge/append`,
    token,
    request
  )
}

/**
 * Get specific exercise info (for wrong question book / favorites, independent of courses)
 */
export async function getChallengeExercise(
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
    `/api/learning-path/challenge/exercise/${exerciseId}`,
    token
  )
}

// ========================================
// Mastery Progress APIs (精进之路进度)
// ========================================

export interface SaveMasteryExerciseProgressRequest {
  course_id: number
  chapter_id: number
  section_id?: number  // 小节ID，用于小节级掌握度聚合
  question_id: number
  question_type?: 'base' | 'enhanced'
  exercise_key?: string
  is_completed: boolean
  is_correct: boolean
  user_answer?: string
  correct_answer?: string
  attempt_count?: number
}

export interface BKTDebugInfo {
  section_id?: number
  knowledge_points: string[]
  counted_for_mastery: boolean
  not_counted_reason?: string
  mastery_changes: Array<{
    knowledge_point: string
    p_l_before: number
    p_l_after: number
  }>
  section_mastery: number
  chapter_mastery: number
}

export interface SaveMasteryExerciseProgressResponse {
  success: boolean
  progress_id?: string
  message: string
  bkt_debug?: BKTDebugInfo
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

  const response = await post<SaveMasteryExerciseProgressResponse>(
    '/api/learning-path/mastery/progress/exercise',
    token,
    request
  )

  // 在浏览器控制台显示后端返回的 BKT 调试信息
  if (response.bkt_debug) {
    const debug = response.bkt_debug
    if (!debug.counted_for_mastery && debug.not_counted_reason) {
    }
    for (const change of debug.mastery_changes) {
      const before = (change.p_l_before * 100).toFixed(1)
      const after = (change.p_l_after * 100).toFixed(1)
      const diff = ((change.p_l_after - change.p_l_before) * 100).toFixed(1)
      const arrow = change.p_l_after > change.p_l_before ? '↑' : (change.p_l_after < change.p_l_before ? '↓' : '→')
    }
  } else {
  }

  return response
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

// ========================================
// Recent Arena Exercises API (最近挑战练习)
// ========================================

export interface RecentArenaExercise {
  exercise_id: number
  title: string
  is_correct: boolean
  difficulty: number
}

/**
 * 获取挑战之路最近练习的题目（含正确情况）- 全局，不关联课程
 */
export async function getRecentArenaExercises(
  token: string,
  limit: number = 3
): Promise<RecentArenaExercise[]> {
  return get<RecentArenaExercise[]>(
    `/api/learning-path/challenge/recent?limit=${limit}`,
    token
  )
}

// ========================================
// BKT Mastery APIs (四层聚合掌握度)
// ========================================

export interface KnowledgePointMastery {
  name: string
  p_l: number
  is_mastered: boolean
  total_attempts: number
  correct_attempts: number
}

export interface SectionMasteryResponse {
  section_id: number
  chapter_id: number
  mastery_score: number
  bkt_aggregated_p_l: number
  knowledge_points_count: number
  mastered_points_count: number
  is_completed: boolean
  knowledge_points: KnowledgePointMastery[]
}

export interface ChapterMasterySummary {
  chapter_id: number
  mastery_score: number
  is_completed: boolean
}

export interface CourseMasteryResponse {
  course_id: number
  course_name: string
  mastery_score: number
  progress_percentage: number
  chapters_count: number
  completed_chapters: number
  is_completed: boolean
  chapters: ChapterMasterySummary[]
}

/**
 * 获取小节掌握度（BKT 聚合）
 */
export async function getSectionMastery(
  sectionId: number,
  token: string
): Promise<SectionMasteryResponse> {
  return get<SectionMasteryResponse>(
    `/api/learning-path/mastery/section/${sectionId}`,
    token
  )
}

/**
 * 获取课程掌握度（BKT 四层聚合顶层）
 */
export async function getCourseMastery(
  courseId: number,
  token: string
): Promise<CourseMasteryResponse> {
  return get<CourseMasteryResponse>(
    `/api/learning-path/mastery/course/${courseId}`,
    token
  )
}
