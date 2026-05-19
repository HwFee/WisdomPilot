/**
 * Sections API - 小节相关的API调用
 */

import { getStoredToken } from './auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 知识点详情类型
export interface KnowledgePointDetail {
  id: number
  order_index: number
  name: string
  content: string | null
  summary: string | null
  code_example: string | null
  code_language: string
  code_explanation: string | null
  difficulty: number
  importance: number
  tips: string[] | null
  common_mistakes: string[] | null
}

// 类型定义
export interface SectionSummary {
  id: number
  chapter_id: number
  title: string
  description: string | null
  order_index: number
  estimated_minutes: number
  is_completed: boolean
  mastery_score?: number  // BKT 聚合掌握度 0-100
}

export interface SectionDetail {
  id: number
  chapter_id: number
  title: string
  description: string | null
  content: string | null
  order_index: number
  estimated_minutes: number
  learning_objectives: string[] | null
  is_completed: boolean
  last_position: string
  knowledge_points: KnowledgePointDetail[]  // 新增：知识点列表
}

export interface SectionListResponse {
  sections: SectionSummary[]
  total: number
}

export interface SectionDetailResponse {
  section: SectionDetail
}

export interface SectionProgressResponse {
  section_id: number
  is_completed: boolean
  last_position: string
  completed_at: string | null
}

export interface CurrentPositionResponse {
  course_id: number
  chapter_id: number
  section_id: number
  position: string
  chapter_title: string | null
  section_title: string | null
}

/**
 * 获取章节的所有小节（含用户完成状态）
 */
export async function getChapterSections(
  chapterId: number,
  token?: string
): Promise<SectionListResponse> {
  const authToken = token || getStoredToken()
  if (!authToken) {
    throw new Error('未登录')
  }

  const response = await fetch(`${API_URL}/api/courses/chapters/${chapterId}/sections`, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '获取小节列表失败')
  }

  return response.json()
}

/**
 * 获取小节详情（含内容）
 */
export async function getSection(
  sectionId: number,
  token?: string
): Promise<SectionDetailResponse> {
  const authToken = token || getStoredToken()
  if (!authToken) {
    throw new Error('未登录')
  }

  const response = await fetch(`${API_URL}/api/courses/sections/${sectionId}`, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '获取小节详情失败')
  }

  return response.json()
}

/**
 * 保存小节学习进度
 */
export async function saveSectionProgress(
  sectionId: number,
  position: 'content' | 'quiz',
  isCompleted: boolean = false,
  token?: string
): Promise<SectionProgressResponse> {
  const authToken = token || getStoredToken()
  if (!authToken) {
    throw new Error('未登录')
  }

  const response = await fetch(`${API_URL}/api/courses/sections/${sectionId}/progress`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      position,
      is_completed: isCompleted,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '保存进度失败')
  }

  return response.json()
}

/**
 * 获取用户当前学习位置
 */
export async function getCurrentPosition(
  courseId: number,
  token?: string
): Promise<CurrentPositionResponse | null> {
  const authToken = token || getStoredToken()
  if (!authToken) {
    throw new Error('未登录')
  }

  const response = await fetch(`${API_URL}/api/courses/${courseId}/current-position`, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    if (response.status === 404) {
      return null // 还没有学习进度
    }
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '获取学习位置失败')
  }

  return response.json()
}
