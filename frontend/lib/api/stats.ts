/**
 * Stats API - Learning statistics and progress endpoints
 */

import {
  ChapterProgress,
  LearningSession,
  LearningStatistics,
  Activity,
  UpdateProgressRequest,
  StartSessionRequest,
  EndSessionRequest,
  UpdateSubsectionRequest,
} from "@/types/api";
import { get, post, put, API_BASE_URL } from "./client";

// ========================================
// Progress API Functions
// ========================================

export async function getUserProgress(
  token: string,
): Promise<ChapterProgress[]> {
  return get<ChapterProgress[]>("/api/stats/progress", token);
}

export async function getChapterProgress(
  token: string,
  chapterId: number,
): Promise<ChapterProgress> {
  return get<ChapterProgress>(`/api/stats/progress/${chapterId}`, token);
}

export async function updateChapterProgress(
  token: string,
  chapterId: number,
  data: UpdateProgressRequest,
): Promise<ChapterProgress> {
  return put<ChapterProgress>(`/api/stats/progress/${chapterId}`, token, data);
}

// ========================================
// Session API Functions
// ========================================

export async function startLearningSession(
  token: string,
  chapterId: number,
  subsectionIndex: number = 0,
): Promise<LearningSession> {
  return post<LearningSession>("/api/stats/sessions/start", token, {
    chapter_id: chapterId,
    subsection_index: subsectionIndex,
  });
}

export async function startStageSession(
  token: string,
  stageId: number,
): Promise<LearningSession> {
  return post<LearningSession>("/api/stats/sessions/start", token, {
    chapter_id: stageId, // 使用 stageId 作为 chapter_id
    subsection_index: 0,
  });
}

export async function endLearningSession(
  token: string,
  durationSeconds: number,
  chapterId?: number,
): Promise<LearningSession> {
  return post<LearningSession>("/api/stats/sessions/end", token, {
    duration_seconds: durationSeconds,
    chapter_id: chapterId ?? null,
  });
}

/**
 * End a learning session using keepalive fetch — survives page navigation/unmount.
 * Use this in cleanup effects and exit handlers where navigation may cancel normal fetch.
 * Fire-and-forget: does not return a Promise.
 */
export function endLearningSessionKeepalive(
  token: string,
  durationSeconds: number,
  chapterId?: number,
): void {

  import("./client").then(({ postKeepalive }) => {
    postKeepalive("/api/stats/sessions/end", token, {
      duration_seconds: durationSeconds,
      chapter_id: chapterId ?? null,
    }).then(() => {
    }).catch((err) => {
      console.error("[学习时长-API] postKeepalive 请求失败:", err);
    });
  });
}

export async function getActiveSession(
  token: string,
): Promise<LearningSession | null> {
  return get<LearningSession | null>("/api/stats/sessions/active", token);
}

export async function updateSessionSubsection(
  token: string,
  subsectionIndex: number,
): Promise<LearningSession> {
  return post<LearningSession>("/api/stats/sessions/subsection", token, {
    subsection_index: subsectionIndex,
  });
}

export async function getLearningSessions(
  token: string,
  limit: number = 50,
): Promise<LearningSession[]> {
  return get<LearningSession[]>(`/api/stats/sessions?limit=${limit}`, token);
}

// ========================================
// Statistics API Functions
// ========================================

export async function getLearningStatistics(
  token: string,
): Promise<LearningStatistics> {
  return get<LearningStatistics>("/api/stats/statistics", token);
}

export async function getActivityHistory(
  token: string,
  limit: number = 20,
): Promise<Activity[]> {
  return get<Activity[]>(`/api/stats/activities?limit=${limit}`, token);
}

// ========================================
// Exercise Answers API Functions
// ========================================

export interface ExerciseAnswer {
  subsection_index: number;
  exercise_id: number;
  correct_answer_index: number;
}

export interface ChapterExerciseAnswers {
  chapter_id: number;
  answers: ExerciseAnswer[];
}

export async function getChapterExerciseAnswers(
  token: string,
  chapterId: number,
): Promise<ChapterExerciseAnswers> {
  return get<ChapterExerciseAnswers>(
    `/api/stats/exercises/answers/${chapterId}`,
    token,
  );
}

// Re-export types
export type {
  ChapterProgress,
  LearningSession,
  LearningStatistics,
  Activity,
  UpdateProgressRequest,
};
