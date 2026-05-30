/**
 * Solutions API - 题解广场接口
 */

import { get, post, put, del } from './client'

export interface SolutionCreate {
  title: string
  content?: string
  problem_link?: string
  tags?: string[]
  is_announcement?: boolean
}

export interface SolutionUpdate {
  title?: string
  content?: string
  problem_link?: string
  tags?: string[]
}

export interface SolutionResponse {
  id: number
  user_id: string
  username: string
  title: string
  content: string
  problem_link?: string
  tags: string[]
  is_pinned: boolean
  is_announcement: boolean
  view_count: number
  like_count: number
  created_at: string
  updated_at: string
  hot_score: number
}

export interface SolutionListResponse {
  solutions: SolutionResponse[]
  total: number
  page: number
  limit: number
}

export interface SolutionSummary {
  id: number
  user_id: string
  username: string
  title: string
  is_pinned: boolean
  is_announcement: boolean
  view_count: number
  like_count: number
  created_at: string
  hot_score: number
}

export async function createSolution(token: string, data: SolutionCreate): Promise<SolutionResponse> {
  return post<SolutionResponse>('/api/solutions', token, data)
}

export async function getSolutions(token: string, params?: {
  page?: number
  limit?: number
  sort?: 'hot' | 'new' | 'pinned'
}): Promise<SolutionListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.page) searchParams.append('page', String(params.page))
  if (params?.limit) searchParams.append('limit', String(params.limit))
  if (params?.sort) searchParams.append('sort', params.sort)
  const query = searchParams.toString()
  return get<SolutionListResponse>(`/api/solutions${query ? `?${query}` : ''}`, token)
}

export async function getSolutionSummary(token: string, limit = 10): Promise<SolutionSummary[]> {
  return get<SolutionSummary[]>(`/api/solutions/summary?limit=${limit}`, token)
}

export async function getSolution(token: string, id: number): Promise<SolutionResponse> {
  return get<SolutionResponse>(`/api/solutions/${id}`, token)
}

export async function updateSolution(token: string, id: number, data: SolutionUpdate): Promise<SolutionResponse> {
  return put<SolutionResponse>(`/api/solutions/${id}`, token, data)
}

export async function deleteSolution(token: string, id: number): Promise<void> {
  return del<void>(`/api/solutions/${id}`, token)
}

export async function likeSolution(token: string, id: number): Promise<SolutionResponse> {
  return post<SolutionResponse>(`/api/solutions/${id}/like`, token, {})
}

export async function pinSolution(token: string, id: number): Promise<SolutionResponse> {
  return post<SolutionResponse>(`/api/solutions/${id}/pin`, token, {})
}
