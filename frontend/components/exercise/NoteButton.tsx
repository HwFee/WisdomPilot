'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { FileText, Loader2 } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { getNotes, type NoteResponse } from '@/lib/api/notes'

interface NoteButtonProps {
  /** 课程ID */
  courseId: number
  /** 原始练习题ID */
  exerciseId?: number
  /** 章节ID（精进之路来源） */
  chapterId?: number
  /** 小节ID */
  sectionId?: number
  /** 题目内容快照 */
  exerciseContent?: {
    title?: string
    text?: string
    description?: string
    options?: string[]
  }
  /** 知识点 */
  knowledgePoints?: string[]
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否显示标签 */
  showLabel?: boolean
  /** 语言 */
  lang?: 'zh' | 'en'
  /** 笔记状态变化回调 */
  onNoteChange?: (note: NoteResponse | null) => void
  /** 点击按钮时调用，由父组件处理打开编辑器 */
  onClick?: (existingNote: NoteResponse | null) => void
  /** 改变此值会触发重新检查笔记状态 */
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
  const [existingNote, setExistingNote] = useState<NoteResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const prevRefreshKeyRef = useRef(refreshKey)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  // 检查是否已有笔记
  useEffect(() => {
    let cancelled = false

    const checkNote = async () => {
      const token = getStoredToken()
      if (!token || !exerciseId) return

      setIsLoading(true)
      try {
        // 通过搜索来检查是否存在笔记
        const result = await getNotes(token, { chapterId, limit: 100 })
        if (cancelled) return

        // 查找关联到该题目的笔记
        const note = result.notes.find((n) => n.exercise_id === exerciseId)
        if (note) {
          setHasNote(true)
          setExistingNote(note)
          onNoteChange?.(note)
        } else {
          setHasNote(false)
          setExistingNote(null)
          onNoteChange?.(null)
        }
      } catch (error) {
        console.error('[NoteButton] 检查笔记失败:', error)
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    checkNote()
    return () => {
      cancelled = true
    }
  }, [exerciseId, chapterId, onNoteChange, refreshKey])

  // 检测 refreshKey 变化时强制重新检查
  useEffect(() => {
    if (refreshKey !== undefined && refreshKey !== prevRefreshKeyRef.current) {
      prevRefreshKeyRef.current = refreshKey
    }
  }, [refreshKey])

  const handleClick = useCallback(() => {
    onClick?.(existingNote)
  }, [existingNote, onClick])

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
        handleClick()
      }}
      disabled={isLoading}
      className={`
        flex items-center justify-center rounded-lg transition-all duration-200
        ${showLabel ? 'px-2.5 gap-1' : sizeClasses[size]}
        ${
          hasNote
            ? 'bg-primary/20 text-primary hover:bg-primary/30'
            : 'bg-muted/50 text-muted-foreground hover:bg-primary/10 hover:text-primary'
        }
        ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      title={hasNote ? t('查看/编辑笔记', 'View/Edit Note') : t('记笔记', 'Add Note')}
    >
      {isLoading ? (
        <Loader2 className={`${iconSizes[size]} animate-spin`} />
      ) : (
        <FileText className={iconSizes[size]} />
      )}
      {showLabel && (
        <span className="text-sm">
          {hasNote ? t('已记笔记', 'Noted') : t('笔记', 'Note')}
        </span>
      )}
    </button>
  )
}
