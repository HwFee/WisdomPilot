'use client'

import { useState, useCallback, useEffect, useRef, useTransition } from 'react'
import { Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getStoredToken } from '@/lib/api'
import {
  addFavorite,
  removeFavorite,
  checkFavorite,
} from '@/lib/api/favorites'
import type { FavoriteCreate } from '@/types/api'
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

interface FavoriteButtonProps {
  exerciseKey?: string
  courseId?: number
  exerciseId?: number
  chapterId?: number
  sectionId?: number
  exerciseContent?: {
    title?: string
    text?: string
    description?: string
    options?: string[]
  }
  exerciseType?: string
  exerciseDifficulty?: number
  knowledgePoints?: string[]
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  lang?: 'zh' | 'en'
  onFavoriteChange?: (isFavorited: boolean) => void
}

export function FavoriteButton({
  exerciseKey,
  courseId,
  exerciseId,
  chapterId,
  sectionId,
  exerciseContent,
  exerciseType,
  exerciseDifficulty,
  knowledgePoints,
  size = 'md',
  showLabel = false,
  lang = 'zh',
  onFavoriteChange,
}: FavoriteButtonProps) {
  const [isFavorited, setIsFavorited] = useState(false)
  const favoriteIdRef = useRef<string | null>(null)
  const [isPending, startTransition] = useTransition()

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  useEffect(() => {
    let cancelled = false

    const checkStatus = async () => {
      const token = getStoredToken()
      if (!token) return
      if (!exerciseKey && !exerciseId) return

      try {
        const result = await checkFavorite(token, exerciseKey, exerciseId)
        if (cancelled) return
        setIsFavorited(result.is_favorited)
        favoriteIdRef.current = result.favorite_id
      } catch (error) {
        console.error('[FavoriteButton] checkStatus error:', error)
        if (!cancelled) {
          setIsFavorited(false)
          favoriteIdRef.current = null
        }
      }
    }

    checkStatus()
    return () => {
      cancelled = true
    }
  }, [exerciseKey, exerciseId, courseId])

  const handleToggleFavorite = useCallback(async () => {
    const token = getStoredToken()
    if (!token) return
    if (!exerciseKey && !exerciseId) return

    startTransition(async () => {
      try {
        if (isFavorited && favoriteIdRef.current) {
          await removeFavorite(token, favoriteIdRef.current)
          setIsFavorited(false)
          favoriteIdRef.current = null
          onFavoriteChange?.(false)
        } else {
          const data: FavoriteCreate = {
            exercise_key: exerciseKey || '',
            course_id: courseId ?? 0,
            exercise_id: exerciseId,
            chapter_id: chapterId,
            section_id: sectionId,
            exercise_content: exerciseContent,
            exercise_type: exerciseType,
            exercise_difficulty: exerciseDifficulty,
            knowledge_points: knowledgePoints,
          }
          const response = await addFavorite(token, data)
          setIsFavorited(true)
          favoriteIdRef.current = response.id
          onFavoriteChange?.(true)
        }
      } catch (error) {
        console.error('[FavoriteButton] handleToggleFavorite error:', error)
      }
    })
  }, [
    isFavorited,
    favoriteIdRef,
    exerciseKey,
    courseId,
    exerciseId,
    chapterId,
    sectionId,
    exerciseContent,
    exerciseType,
    exerciseDifficulty,
    knowledgePoints,
    onFavoriteChange,
  ])

  return (
    <Button
      type="button"
      variant="ghost"
      size={showLabel ? 'default' : 'icon'}
      onClick={(e) => {
        e.stopPropagation()
        handleToggleFavorite()
      }}
      disabled={isPending}
      className={cn(
        showLabel ? 'px-2.5 gap-1' : SIZE_CLASSES[size],
        isFavorited
          ? 'bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30'
          : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-yellow-500',
        isPending && 'opacity-50 cursor-not-allowed'
      )}
      title={
        isFavorited
          ? t('取消收藏', 'Remove from favorites')
          : t('收藏', 'Add to favorites')
      }
    >
      <Star
        className={cn(
          ICON_SIZES[size],
          isFavorited && 'fill-yellow-500 text-yellow-500'
        )}
      />
      {showLabel && (
        <span className="text-sm">
          {isFavorited ? t('已收藏', 'Favorited') : t('收藏', 'Favorite')}
        </span>
      )}
    </Button>
  )
}
