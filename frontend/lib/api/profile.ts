/**
 * Profile API - User profile endpoints
 */

import {
  UserProfileResponse,
  UpdateProfileRequest,
  AddXpRequest,
  CheckinResponse,
  CheckinStatusResponse,
} from '@/types/api'
import { get, post, put } from './client'

// ========================================
// Profile API Functions
// ========================================

export async function getProfile(token: string): Promise<UserProfileResponse> {
  return get<UserProfileResponse>('/api/users/profile', token)
}

export async function updateProfile(
  token: string,
  request: UpdateProfileRequest
): Promise<UserProfileResponse> {
  return put<UserProfileResponse>('/api/users/profile', token, request)
}

export async function addXp(
  token: string,
  xpAmount: number
): Promise<{ xp: number; level: number; xp_for_next_level: number }> {
  // 后端使用 query 参数而非 body
  return post<{ xp: number; level: number; xp_for_next_level: number }>(
    `/api/users/xp?xp_amount=${xpAmount}`,
    token
  )
}

// ========================================
// Checkin API Functions
// ========================================

export async function checkin(token: string): Promise<CheckinResponse> {
  return post<CheckinResponse>('/api/users/checkin', token)
}

export async function getCheckinStatus(token: string): Promise<CheckinStatusResponse> {
  return get<CheckinStatusResponse>('/api/users/checkin/status', token)
}

// Re-export types
export type { UserProfileResponse, UpdateProfileRequest, CheckinResponse, CheckinStatusResponse }
