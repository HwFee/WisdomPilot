/**
 * Courses API - Course and chapter endpoints
 */

import {
  CourseListResponse,
  CourseDetailResponse,
  ChapterDetailResponse,
  CourseSummary,
  CourseDetail,
  ChapterDetail,
} from '@/types/api'
import { get, API_BASE_URL } from './client'

// ========================================
// Course Progress Types
// ========================================

export interface CourseProgress {
  course_id: number
  course_code: string
  course_name: string
  progress: number
  completed_stages: number
  total_stages: number
  current_chapter: string | null
  current_section: string | null
  mastery_score: number | null
  arena_tier: string | null
  arena_score: number | null
}

export interface CourseProgressResponse {
  courses: CourseProgress[]
}

export interface TodayStatsResponse {
  exercises: number
  correct: number
  accuracy: number
  time_minutes: number
}

// ========================================
// Courses API Functions
// ========================================

export async function getCourses(token?: string): Promise<CourseListResponse> {
  const url = `${API_BASE_URL}/api/courses`

  if (token) {
    return get<CourseListResponse>('/api/courses', token)
  }

  // Public access without token
  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch courses')
  }
  return response.json()
}

export async function getCourse(courseId: number, token?: string): Promise<CourseDetailResponse> {
  const url = `${API_BASE_URL}/api/courses/${courseId}`

  if (token) {
    return get<CourseDetailResponse>(`/api/courses/${courseId}`, token)
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch course')
  }
  return response.json()
}

export async function getCourseByCode(code: string, token?: string): Promise<CourseDetailResponse> {
  const url = `${API_BASE_URL}/api/courses/code/${code}`

  if (token) {
    return get<CourseDetailResponse>(`/api/courses/code/${code}`, token)
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch course')
  }
  return response.json()
}

/**
 * Get progress for all courses for the current user
 */
export async function getUserCourseProgress(token: string): Promise<CourseProgressResponse> {
  return get<CourseProgressResponse>('/api/courses/users/me/course-progress', token)
}

/**
 * Get today's learning statistics
 */
export async function getTodayStats(token: string): Promise<TodayStatsResponse> {
  return get<TodayStatsResponse>('/api/stats/today', token)
}

// ========================================
// Chapters API Functions
// ========================================

export async function getChapter(
  chapterId: number,
  token?: string
): Promise<ChapterDetailResponse> {
  const url = `${API_BASE_URL}/api/chapters/${chapterId}`

  if (token) {
    return get<ChapterDetailResponse>(`/api/chapters/${chapterId}`, token)
  }

  const response = await fetch(url)
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to fetch chapter')
  }
  return response.json()
}

// Re-export types
export type { CourseSummary, CourseDetail, ChapterDetail }
