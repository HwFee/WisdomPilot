/**
 * Achievements API - Achievement endpoints
 */

import {
  AchievementListResponse,
  AchievementWithEarnedResponse,
  AchievementSummary,
  AchievementDetail,
  UserAchievementsResponse,
  UserRankResponse,
} from '@/types/api'
import { get, API_BASE_URL } from './client'

// ========================================
// Achievements API Functions
// ========================================

export async function getAchievements(token?: string): Promise<AchievementListResponse> {
  const url = `${API_BASE_URL}/api/achievements`

  if (token) {
    return get<AchievementListResponse>('/api/achievements', token)
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch achievements')
  }
  return response.json()
}

export async function getAchievementsWithEarned(
  token: string
): Promise<AchievementWithEarnedResponse> {
  // 使用正确的端点 /api/achievements/me 而非 /api/achievements/earned
  return get<AchievementWithEarnedResponse>('/api/achievements/me', token)
}

export async function getAchievement(
  achievementId: number,
  token?: string
): Promise<{ achievement: AchievementDetail }> {
  // 使用正确的端点
  const url = `${API_BASE_URL}/api/achievements/${achievementId}`

  if (token) {
    return get<{ achievement: AchievementDetail }>(
      `/api/achievements/${achievementId}`,
      token
    )
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch achievement')
  }
  return response.json()
}

export async function getUserAchievements(token: string): Promise<UserAchievementsResponse> {
  return get<UserAchievementsResponse>('/api/achievements/me', token)
}

export async function getLeaderboard(
  limit: number = 10,
  token?: string
): Promise<UserRankResponse[]> {
  const url = `${API_BASE_URL}/api/achievements/leaderboard?limit=${limit}`

  if (token) {
    return get<UserRankResponse[]>(`/api/achievements/leaderboard?limit=${limit}`, token)
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch leaderboard')
  }
  return response.json()
}

export async function getUserRank(token: string): Promise<UserRankResponse> {
  return get<UserRankResponse>('/api/achievements/rank', token)
}

// Re-export types
export type { AchievementSummary, AchievementDetail }
