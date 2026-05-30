/**
 * Trends API - Statistics trend endpoints
 */

import {
  DailyExercisesTrendResponse,
  DailyAccuracyTrendResponse,
  DailyTimeTrendResponse,
} from '@/types/api'
import { get } from './client'

// ========================================
// Trends API Functions
// ========================================

export async function getExercisesTrend(
  token: string,
  days: number = 7
): Promise<DailyExercisesTrendResponse> {
  return get<DailyExercisesTrendResponse>(`/api/stats/trends/exercises?days=${days}`, token)
}

export async function getAccuracyTrend(
  token: string,
  days: number = 7
): Promise<DailyAccuracyTrendResponse> {
  return get<DailyAccuracyTrendResponse>(`/api/stats/trends/accuracy?days=${days}`, token)
}

export async function getTimeTrend(
  token: string,
  days: number = 7
): Promise<DailyTimeTrendResponse> {
  return get<DailyTimeTrendResponse>(`/api/stats/trends/time?days=${days}`, token)
}

// Re-export types
export type {
  DailyExercisesTrendResponse,
  DailyAccuracyTrendResponse,
  DailyTimeTrendResponse,
}
