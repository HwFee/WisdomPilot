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
