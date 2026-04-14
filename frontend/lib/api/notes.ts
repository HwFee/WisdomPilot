/**
 * Notes API - User notes endpoints
 */

import {
  NoteCreate,
  NoteUpdate,
  NoteResponse,
  NoteListResponse,
  NoteCountResponse,
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
  chapterId?: number,
  limit: number = 50,
  offset: number = 0
): Promise<NoteListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })
  if (chapterId !== undefined) {
    params.append('chapter_id', String(chapterId))
  }
  return get<NoteListResponse>(`/api/notes?${params.toString()}`, token)
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

// Re-export types
export type {
  NoteCreate,
  NoteUpdate,
  NoteResponse,
  NoteListResponse,
  NoteCountResponse,
}
