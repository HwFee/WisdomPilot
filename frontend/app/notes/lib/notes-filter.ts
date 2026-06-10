import type { NoteResponse } from '@/types/api'

export function filterNotesByTags(
  notes: NoteResponse[],
  selectedTags: string[],
): NoteResponse[] {
  if (selectedTags.length === 0) return notes
  return notes.filter((note) =>
    selectedTags.every((tag) => note.tags?.includes(tag)),
  )
}

export function filterNotesBySearch(
  notes: NoteResponse[],
  query: string,
): NoteResponse[] {
  if (!query) return notes
  const lowerQuery = query.toLowerCase()
  return notes.filter(
    (note) =>
      note.title?.toLowerCase().includes(lowerQuery) ||
      note.content.toLowerCase().includes(lowerQuery) ||
      note.knowledge_points?.some((kp) => kp.toLowerCase().includes(lowerQuery)),
  )
}
