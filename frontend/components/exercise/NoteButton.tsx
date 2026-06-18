'use client'

import { useState, useCallback, useEffect, useRef, useTransition } from 'react'
import { FileText, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getStoredToken } from '@/lib/api'
import { getNotes, type NoteResponse } from '@/lib/api/notes'
import { cn } from '@/lib/utils'

const SIZE_CLASSES = {
  sm: 'size-9',
  md: 'size-10',
  lg: 'size-11',
} as const

const ICON_SIZES = {
  sm: 'size-3.5',
  md: 'size-4',
  lg: 'size-5',
} as const

interface NoteButtonProps {
  courseId: number
  exerciseId?: number
  chapterId?: number
  sectionId?: number
  exerciseContent?: {
    title?: string
    text?: string
    description?: string
    options?: string[]
  }
  knowledgePoints?: string[]
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  lang?: 'zh' | 'en'
  onNoteChange?: (note: NoteResponse | null) => void
  onClick?: (existingNote: NoteResponse | null) => void
  refreshKey?: number | string
}

export function NoteButton({
  courseId,
  exerciseId,
  chapterId,
  knowledgePoints,
  size = 'md',
  showLabel = false,
  lang = 'zh',
  onNoteChange,
  onClick,
  refreshKey,
}: NoteButtonProps) {
  const [hasNote, setHasNote] = useState(false)
  const existingNoteRef = useRef<NoteResponse | null>(null)
  const [isPending, startTransition] = useTransition()
  const prevRefreshKeyRef = useRef(refreshKey)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  useEffect(() => {
    const token = getStoredToken()
    if (!token || !exerciseId) return

    startTransition(async () => {
      try {
        const result = await getNotes(token, { chapterId, limit: 100 })
        const note = result.notes.find((n) => n.exercise_id === exerciseId)
        if (note) {
          setHasNote(true)
          existingNoteRef.current = note
          onNoteChange?.(note)
        } else {
          setHasNote(false)
          existingNoteRef.current = null
          onNoteChange?.(null)
        }
      } catch (error) {
        console.error('[NoteButton] 检查笔记失败:', error)
      }
    })
  }, [exerciseId, chapterId, onNoteChange, refreshKey])

  useEffect(() => {
    if (refreshKey !== undefined && refreshKey !== prevRefreshKeyRef.current) {
      prevRefreshKeyRef.current = refreshKey
    }
  }, [refreshKey])

  const handleClick = useCallback(() => {
    onClick?.(existingNoteRef.current)
  }, [onClick])

  return (
    <Button
      type="button"
      variant="ghost"
      size={showLabel ? 'default' : 'icon'}
      onClick={(e) => {
        e.stopPropagation()
        handleClick()
      }}
      disabled={isPending}
      className={cn(
        showLabel ? 'px-2.5 gap-1' : SIZE_CLASSES[size],
        hasNote
          ? 'bg-primary/20 text-primary hover:bg-primary/30'
          : 'bg-muted/50 text-muted-foreground hover:bg-primary/10 hover:text-primary',
        isPending && 'opacity-50 cursor-not-allowed'
      )}
      title={hasNote ? t('查看/编辑笔记', 'View/Edit Note') : t('记笔记', 'Add Note')}
    >
      {isPending ? (
        <Loader2 className={cn(ICON_SIZES[size], 'animate-spin')} />
      ) : (
        <FileText className={ICON_SIZES[size]} />
      )}
      {showLabel && (
        <span className="text-sm">
          {hasNote ? t('已记笔记', 'Noted') : t('笔记', 'Note')}
        </span>
      )}
    </Button>
  )
}
