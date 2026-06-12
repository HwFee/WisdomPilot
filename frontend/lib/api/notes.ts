/**
 * Notes API - User notes endpoints
 */

import {
  NoteCreate,
  NoteUpdate,
  NoteFromQuestion,
  NoteResponse,
  NoteListResponse,
  NoteCountResponse,
  NoteSearchResponse,
  NoteExportRequest,
  NoteTagCreate,
  NoteTagUpdate,
  NoteTagResponse,
  NoteTagListResponse,
} from '@/types/api'
import { get, post, put, del } from './client'

// ========================================
// Notes API Functions
// ========================================

export async function createNote(
  token: string,
  data: NoteCreate
): Promise<NoteResponse> {
  return post<NoteResponse>('/api/notes', token, data)
}

export async function getNotes(
  token: string,
  options?: {
    chapterId?: number
    tags?: string[]
    limit?: number
    offset?: number
  }
): Promise<NoteListResponse> {
  const params = new URLSearchParams()
  if (options?.chapterId !== undefined) {
    params.append('chapter_id', String(options.chapterId))
  }
  if (options?.tags && options.tags.length > 0) {
    params.append('tags', options.tags.join(','))
  }
  params.append('limit', String(options?.limit ?? 50))
  params.append('offset', String(options?.offset ?? 0))
  return get<NoteListResponse>(`/api/notes?${params.toString()}`, token)
}

export async function searchNotes(
  token: string,
  query: string,
  options?: {
    tags?: string[]
    chapterId?: number
    limit?: number
  }
): Promise<NoteSearchResponse> {
  const params = new URLSearchParams({ q: query })
  if (options?.tags && options.tags.length > 0) {
    params.append('tags', options.tags.join(','))
  }
  if (options?.chapterId !== undefined) {
    params.append('chapter_id', String(options.chapterId))
  }
  params.append('limit', String(options?.limit ?? 50))
  return get<NoteSearchResponse>(`/api/notes/search?${params.toString()}`, token)
}

async function getNote(
  token: string,
  noteId: string
): Promise<NoteResponse> {
  return get<NoteResponse>(`/api/notes/${noteId}`, token)
}

export async function getNotesCount(token: string): Promise<NoteCountResponse> {
  return get<NoteCountResponse>('/api/notes/count', token)
}

export async function updateNote(
  token: string,
  noteId: string,
  data: NoteUpdate
): Promise<NoteResponse> {
  return put<NoteResponse>(`/api/notes/${noteId}`, token, data)
}

export async function deleteNote(
  token: string,
  noteId: string
): Promise<{ success: boolean }> {
  return del<{ success: boolean }>(`/api/notes/${noteId}`, token)
}

export async function createNoteFromQuestion(
  token: string,
  data: NoteFromQuestion
): Promise<NoteResponse> {
  return post<NoteResponse>('/api/notes/from-question', token, data)
}

export async function exportNote(
  token: string,
  noteId: string
): Promise<Response> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  return fetch(`${apiUrl}/api/notes/export/${noteId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
}

export async function exportNotes(
  token: string,
  data: NoteExportRequest
): Promise<Response> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  return fetch(`${apiUrl}/api/notes/export`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
}

// ========================================
// Note Tags API Functions
// ========================================

export async function createNoteTag(
  token: string,
  data: NoteTagCreate
): Promise<NoteTagResponse> {
  return post<NoteTagResponse>('/api/note-tags', token, data)
}

export async function getNoteTags(
  token: string
): Promise<NoteTagListResponse> {
  return get<NoteTagListResponse>('/api/note-tags', token)
}

async function updateNoteTag(
  token: string,
  tagId: string,
  data: NoteTagUpdate
): Promise<NoteTagResponse> {
  return put<NoteTagResponse>(`/api/note-tags/${tagId}`, token, data)
}

export async function deleteNoteTag(
  token: string,
  tagId: string
): Promise<{ success: boolean }> {
  return del<{ success: boolean }>(`/api/note-tags/${tagId}`, token)
}

// Re-export types
export type {
  NoteCreate,
  NoteUpdate,
  NoteFromQuestion,
  NoteResponse,
  NoteListResponse,
  NoteCountResponse,
  NoteSearchResponse,
  NoteExportRequest,
  NoteTagCreate,
  NoteTagUpdate,
  NoteTagResponse,
  NoteTagListResponse,
}
