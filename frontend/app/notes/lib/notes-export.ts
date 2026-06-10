import { exportNotes } from '@/lib/api/notes'
import { getStoredToken } from '@/lib/api'
import type { NoteResponse } from '@/types/api'

export async function exportAllNotes(notes: NoteResponse[]): Promise<void> {
  const token = getStoredToken()
  if (!token || notes.length === 0) return

  try {
    const response = await exportNotes(token, {
      note_ids: notes.map((n) => n.id),
      format: 'markdown',
    })
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'my_notes.md'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('[笔记] 导出失败:', error)
  }
}
