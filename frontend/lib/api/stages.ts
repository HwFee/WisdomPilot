/**
 * Stages API - 关卡系统接口
 */

import {
  StageListResponse,
  StageDetailResponse,
  StartStageResponse,
  CompletePracticeRequest,
  CompletePracticeResponse,
  StartVerificationResponse,
  SubmitVerificationRequest,
  SubmitVerificationResponse,
  StageExerciseListResponse,
  GenerateExercisesRequest,
  GenerateExercisesResponse,
} from '@/types/stage'
import { get, post } from './client'

// ========================================
// Knowledge Check Types
// ========================================

export interface KnowledgeCheckQuestion {
  id: string
  question: string
  options: string[]
  correct_answer: string
  explanation?: string
  knowledge_point?: string
}

export interface KnowledgeCheckRequest {
  exercise_id?: number
  count?: number
}

export interface KnowledgeCheckResponse {
  questions: KnowledgeCheckQuestion[]
  stage_id: number
  message: string
}

// ========================================
// Stages API Functions
// ========================================

export async function getStage(
  stageId: number,
  token: string
): Promise<StageDetailResponse> {
  return get<StageDetailResponse>(`/api/stages/${stageId}`, token)
}

export async function getCourseStages(
  courseId: number,
  token: string
): Promise<StageListResponse> {
  return get<StageListResponse>(`/api/stages/course/${courseId}`, token)
}

export async function startStage(
  stageId: number,
  token: string
): Promise<StartStageResponse> {
  return post<StartStageResponse>(`/api/stages/${stageId}/start`, token)
}

export async function completePractice(
  stageId: number,
  request: CompletePracticeRequest,
  token: string
): Promise<CompletePracticeResponse> {
  return post<CompletePracticeResponse>(
    `/api/stages/${stageId}/complete`,
    token,
    request
  )
}

export async function startVerification(
  stageId: number,
  token: string
): Promise<StartVerificationResponse> {
  return post<StartVerificationResponse>(`/api/stages/${stageId}/verify`, token)
}

export async function submitVerification(
  stageId: number,
  request: SubmitVerificationRequest,
  token: string
): Promise<SubmitVerificationResponse> {
  return post<SubmitVerificationResponse>(
    `/api/stages/${stageId}/verify/submit`,
    token,
    request
  )
}

// ========================================
// Stage Exercises API Functions
// ========================================

export async function getStageExercises(
  stageId: number,
  token: string,
  limit: number = 20
): Promise<StageExerciseListResponse> {
  return get<StageExerciseListResponse>(
    `/api/stages/${stageId}/exercises?limit=${limit}`,
    token
  )
}

export async function generateStageExercises(
  stageId: number,
  request: GenerateExercisesRequest,
  token: string
): Promise<GenerateExercisesResponse> {
  return post<GenerateExercisesResponse>(
    `/api/stages/${stageId}/exercises/generate`,
    token,
    request
  )
}

// ========================================
// Knowledge Check API Functions
// ========================================

export async function getKnowledgeCheck(
  stageId: number,
  request: KnowledgeCheckRequest,
  token: string
): Promise<KnowledgeCheckResponse> {
  return post<KnowledgeCheckResponse>(
    `/api/stages/${stageId}/knowledge-check`,
    token,
    request
  )
}

// Re-export types
export type {
  StageListResponse,
  StageDetailResponse,
  StartStageResponse,
  CompletePracticeResponse,
  StartVerificationResponse,
  SubmitVerificationResponse,
  StageExerciseListResponse,
  GenerateExercisesResponse,
}
