/**
 * Exercises API - Exercise endpoints
 */

import {
  ExerciseListResponse,
  ExerciseDetail,
  ExerciseSummary,
  ExerciseGenerateRequest,
  ExerciseGenerateResponse,
  ExerciseSubmitRequest,
  ExerciseSubmitResponse,
} from '@/types/api'
import { get, post, API_BASE_URL } from './client'

// ========================================
// Exercises API Functions
// ========================================

export async function getExercises(
  chapterId: number,
  token?: string
): Promise<ExerciseListResponse> {
  const url = `${API_BASE_URL}/api/exercises/chapter/${chapterId}`

  if (token) {
    return get<ExerciseListResponse>(`/api/exercises/chapter/${chapterId}`, token)
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch exercises')
  }
  return response.json()
}

export async function getExercise(
  exerciseId: number,
  token?: string
): Promise<ExerciseDetail> {
  // 使用正确的端点 /api/exercises/detail/{exerciseId}
  const url = `${API_BASE_URL}/api/exercises/detail/${exerciseId}`

  if (token) {
    const response = await get<{ exercise: ExerciseDetail }>(
      `/api/exercises/detail/${exerciseId}`,
      token
    )
    return response.exercise
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch exercise')
  }
  const data = await response.json()
  return data.exercise
}

export async function generateExercises(
  request: ExerciseGenerateRequest,
  token: string
): Promise<ExerciseGenerateResponse> {
  return post<ExerciseGenerateResponse>('/api/exercises/generate', token, request)
}

export async function submitExercise(
  exerciseId: number,
  request: ExerciseSubmitRequest,
  token: string
): Promise<ExerciseSubmitResponse> {
  return post<ExerciseSubmitResponse>(
    `/api/exercises/${exerciseId}/submit`,
    token,
    request
  )
}

export async function verifyExercise(
  exerciseId: number,
  verified: boolean,
  token: string
): Promise<{ id: number; is_verified: boolean; message: string }> {
  return post<{ id: number; is_verified: boolean; message: string }>(
    `/api/exercises/${exerciseId}/verify`,
    token,
    { verified }
  )
}

// Re-export types
export type { ExerciseSummary, ExerciseDetail, ExerciseSubmitResponse }
