'use client'

import { useState, useCallback } from 'react'
import type { NoteResponse } from '@/types/api'

interface EditorState {
  showEditor: boolean
  editingNote: NoteResponse | null
  isFullPageEditor: boolean
}

export function useNoteEditor() {
  const [state, setState] = useState<EditorState>({
    showEditor: false,
    editingNote: null,
    isFullPageEditor: false,
  })

  const openEditor = useCallback((note?: NoteResponse) => {
    setState({
      showEditor: true,
      editingNote: note || null,
      isFullPageEditor: true,
    })
  }, [])

  const closeEditor = useCallback(() => {
    setState({
      showEditor: false,
      editingNote: null,
      isFullPageEditor: false,
    })
  }, [])

  return {
    ...state,
    openEditor,
    closeEditor,
  }
}
