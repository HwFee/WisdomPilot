'use client'

import { useState, useCallback } from 'react'
import { FileText } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { createNote, updateNote, getNotes } from '@/lib/api/notes'
import type { NoteCreate, NoteResponse } from '@/types/api'

interface NoteButtonProps {
  exerciseId?: number
  chapterId?: number
  subsectionIndex?: number
  knowledgePoints?: string[]
  /** Content to pre-fill when creating a note */
  prefillContent?: string
  /** Title to pre-fill when creating a note */
  prefillTitle?: string
  /** Source of the note */
  source?: 'manual' | 'ai_answer' | 'question'
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  lang?: 'zh' | 'en'
  /** Callback when a note is created or updated */
  onNoteChange?: (note: NoteResponse) => void
  /** Callback when the note button is clicked - opens editor */
  onOpenEditor?: (existingNote: NoteResponse | null) => void
}

export function NoteButton({
  exerciseId,
  chapterId,
  subsectionIndex = 0,
  knowledgePoints = [],
  prefillContent,
  prefillTitle,
  source = 'manual',
  size = 'md',
  showLabel = false,
  lang = 'zh',
  onNoteChange,
  onOpenEditor,
}: NoteButtonProps) {
  const [isLoading, setIsLoading] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleCreateNote = useCallback(async () => {
    const token = getStoredToken()
    if (!token) return

    setIsLoading(true)
    try {
      const noteData: NoteCreate = {
        title: prefillTitle || `${t('题目笔记', 'Note')} #${exerciseId || Date.now()}`,
        content: prefillContent || '',
        exercise_id: exerciseId,
        chapter_id: chapterId,
        subsection_index: subsectionIndex,
        knowledge_points: knowledgePoints,
        source,
      }

      const note = await createNote(token, noteData)
      onNoteChange?.(note)
      onOpenEditor?.(note)
    } catch (error) {
      console.error('[笔记] 创建失败:', error)
    } finally {
      setIsLoading(false)
    }
  }, [exerciseId, chapterId, subsectionIndex, knowledgePoints, prefillContent, prefillTitle, source, t, onNoteChange, onOpenEditor])

  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
  }

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }

  return (
    <button
      onClick={(e) => {
        e.stopPropagation()
        // Open editor directly for creating new note
        onOpenEditor?.(null)
      }}
      disabled={isLoading}
      className={`
        flex items-center justify-center rounded-lg transition-all duration-200
        ${showLabel ? 'px-2.5 gap-1' : sizeClasses[size]}
        bg-muted/50 text-muted-foreground hover:bg-primary/10 hover:text-primary
        ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      title={t('记笔记', 'Add Note')}
    >
      <FileText className={iconSizes[size]} />
      {showLabel && (
        <span className="text-sm">{t('笔记', 'Note')}</span>
      )}
    </button>
  )
}
