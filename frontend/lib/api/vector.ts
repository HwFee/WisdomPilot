/**
 * Vector Match API - Exercise recommendation based on adaptive learning
 */

import { post } from './client'

// ========================================
// Types
// ========================================

export interface ExerciseRecommendItem {
  exercise_id: number
  source_id: string
  similarity: number
  difficulty: number
  difficulty_label: string
  type: string
  knowledge_points: string[]
  title: string
  reason: string
  matched_weak_points: string[]
}

export interface KnowledgeState {
  estimated_level: number
  target_difficulty: number
  target_difficulty_label: string
  total_attempts: number
  accuracy: number
}

export interface ExerciseRecommendRequest {
  limit?: number
  min_difficulty?: number
  max_difficulty?: number
  exclude_completed?: boolean
  chapter_id?: number  // 章节ID，用于精进之路
  learning_path?: 'mastery' | 'challenge'  // 学习路径类型
}

export interface ExerciseRecommendResponse {
  user_vector_generated: boolean
  weak_points: string[]
  user_weak_point_count: number
  recommendations: ExerciseRecommendItem[]
  total_candidates: number
  knowledge_state: KnowledgeState | null
}

// ========================================
// API Functions
// ========================================

export async function getExerciseRecommendations(
  token: string,
  request: ExerciseRecommendRequest = {}
): Promise<ExerciseRecommendResponse> {
  return post<ExerciseRecommendResponse>('/api/exercises/recommend', token, request)
}
