/**
 * Challenges API - Challenge endpoints
 */

import {
  ChallengeListResponse,
  ChallengeDetail,
  ChallengeSummary,
  UserChallengesResponse,
  UserChallengeDetail,
} from '@/types/api'
import { get, post, API_BASE_URL } from './client'

// ========================================
// Challenges API Functions
// ========================================

export async function getChallenges(token?: string): Promise<ChallengeListResponse> {
  const url = `${API_BASE_URL}/api/challenges`

  if (token) {
    return get<ChallengeListResponse>('/api/challenges', token)
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch challenges')
  }
  return response.json()
}

export async function getChallenge(
  challengeId: number,
  token?: string
): Promise<{ challenge: ChallengeDetail }> {
  const url = `${API_BASE_URL}/api/challenges/${challengeId}`

  if (token) {
    return get<{ challenge: ChallengeDetail }>(`/api/challenges/${challengeId}`, token)
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch challenge')
  }
  return response.json()
}

export async function startChallenge(
  challengeId: number,
  token: string
): Promise<{ user_challenge: UserChallengeDetail; is_completed: boolean }> {
  return post<{ user_challenge: UserChallengeDetail; is_completed: boolean }>(
    `/api/challenges/${challengeId}/start`,
    token
  )
}

export async function getUserChallenges(token: string): Promise<UserChallengesResponse> {
  return get<UserChallengesResponse>('/api/challenges/user/me', token)
}

// Re-export types
export type { ChallengeSummary, ChallengeDetail, UserChallengeDetail }
