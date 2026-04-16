'use client'

import { useState, useCallback, useEffect } from 'react'
import { Star } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { addFavorite, removeFavorite, getFavorites } from '@/lib/api/favorites'
import type { FavoriteResponse, FavoriteCreate } from '@/types/api'

interface FavoriteButtonProps {
  exerciseId: number
  chapterId?: number
  subsectionIndex?: number
  challengeSessionId?: string
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  lang?: 'zh' | 'en'
  onFavoriteChange?: (isFavorited: boolean) => void
}

export function FavoriteButton({
  exerciseId,
  chapterId,
  subsectionIndex = 0,
  challengeSessionId,
  size = 'md',
  showLabel = false,
  lang = 'zh',
  onFavoriteChange,
}: FavoriteButtonProps) {
  const [isFavorited, setIsFavorited] = useState(false)
  const [favoriteId, setFavoriteId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  // Check if already favorited
  useEffect(() => {
    const checkFavoriteStatus = async () => {
      const token = getStoredToken()
      if (!token) return

      try {
        const data = await getFavorites(token, 100, 0)
        const existing = data.favorites.find(
          (f: FavoriteResponse) =>
            f.exercise_id === exerciseId &&
            f.chapter_id === chapterId &&
            f.subsection_index === subsectionIndex &&
            f.challenge_session_id === challengeSessionId
        )
        if (existing) {
          setIsFavorited(true)
          setFavoriteId(existing.id)
        }
      } catch {
        // Silently handle error - user might not be logged in
      }
    }

    checkFavoriteStatus()
  }, [exerciseId, chapterId, subsectionIndex, challengeSessionId])

  const handleToggleFavorite = useCallback(async () => {
    const token = getStoredToken()
    if (!token) {
      return
    }

    setIsLoading(true)
    try {
      if (isFavorited && favoriteId) {
        // Remove from favorites
        await removeFavorite(token, favoriteId)
        setIsFavorited(false)
        setFavoriteId(null)
        onFavoriteChange?.(false)
      } else {
        // Add to favorites
        const data: FavoriteCreate = {
          exercise_id: exerciseId,
          chapter_id: chapterId,
          subsection_index: subsectionIndex,
          challenge_session_id: challengeSessionId,
        }
        const response = await addFavorite(token, data)
        setIsFavorited(true)
        setFavoriteId(response.id)
        onFavoriteChange?.(true)
      }
    } catch {
      // Handle error silently
    } finally {
      setIsLoading(false)
    }
  }, [isFavorited, favoriteId, exerciseId, chapterId, subsectionIndex, challengeSessionId, onFavoriteChange])

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
      onClick={handleToggleFavorite}
      disabled={isLoading}
      className={`
        flex items-center justify-center rounded-lg transition-all duration-200
        ${sizeClasses[size]}
        ${
          isFavorited
            ? 'bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30'
            : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-yellow-500'
        }
        ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      title={isFavorited ? t('取消收藏', 'Remove from favorites') : t('收藏', 'Add to favorites')}
    >
      <Star
        className={`${iconSizes[size]} ${isFavorited ? 'fill-yellow-500 text-yellow-500' : ''}`}
      />
      {showLabel && (
        <span className="ml-1.5 text-sm">{isFavorited ? t('已收藏', 'Favorited') : t('收藏', 'Favorite')}</span>
      )}
    </button>
  )
}
