'use client'

import { FileText } from 'lucide-react'
import type { NoteResponse } from '@/types/api'

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
  size = 'md',
  showLabel = false,
  lang = 'zh',
  onOpenEditor,
}: NoteButtonProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

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
        onOpenEditor?.(null)
      }}
      className={`
        flex items-center justify-center rounded-lg transition-all duration-200
        ${showLabel ? 'px-2.5 gap-1' : sizeClasses[size]}
        bg-muted/50 text-muted-foreground hover:bg-primary/10 hover:text-primary
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
