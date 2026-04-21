'use client'

import { useMemo } from 'react'
import { Eye, Heart, Pin, Megaphone, Trash2 } from 'lucide-react'
import type { SolutionSummary } from '@/lib/api/solutions'

type CategoryType = 'hot' | 'new' | 'pinned' | 'announcement'

interface SolutionArticleListProps {
  solutions: SolutionSummary[]
  loading: boolean
  activeCategory: CategoryType
  onArticleClick: (id: number) => void
  onDelete?: (id: number) => void
  onLike?: (id: number) => void
  currentUserId?: string
  lang?: 'zh' | 'en'
}

export function SolutionArticleList({
  solutions,
  loading,
  activeCategory,
  onArticleClick,
  onDelete,
  onLike,
  currentUserId,
  lang = 'zh',
}: SolutionArticleListProps) {
  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  const filteredSolutions = useMemo(() => {
    let filtered = [...solutions]

    // Filter by category
    if (activeCategory === 'announcement') {
      filtered = filtered.filter(s => s.is_announcement)
    } else if (activeCategory === 'pinned') {
      filtered = filtered.filter(s => s.is_pinned)
    }

    // Sort
    filtered.sort((a, b) => {
      // Announcements first (unless in announcement tab)
      if (activeCategory !== 'announcement') {
        if (a.is_announcement && !b.is_announcement) return -1
        if (!a.is_announcement && b.is_announcement) return 1
      }
      // Pinned second
      if (a.is_pinned && !b.is_pinned) return -1
      if (!a.is_pinned && b.is_pinned) return 1
      // Then by category
      if (activeCategory === 'hot') return b.hot_score - a.hot_score
      if (activeCategory === 'new' || activeCategory === 'announcement') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }
      return 0
    })

    return filtered
  }, [solutions, activeCategory])

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(hours / 24)

    if (hours < 1) return t('刚刚', 'Just now')
    if (hours < 24) return `${hours}${t('小时前', 'h ago')}`
    if (days < 7) return `${days}${t('天前', 'd ago')}`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="bg-card rounded-2xl border border-border p-8 flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">{t('加载中...', 'Loading...')}</div>
      </div>
    )
  }

  if (filteredSolutions.length === 0) {
    return (
      <div className="bg-card rounded-2xl border border-border p-12 flex flex-col items-center justify-center text-center">
        <p className="text-muted-foreground">{t('暂无内容', 'No content yet')}</p>
      </div>
    )
  }

  return (
    <div className="bg-card rounded-2xl border border-border overflow-hidden">
      <div className="divide-y divide-border">
        {filteredSolutions.map(solution => {
          const isAnnouncementItem = solution.is_announcement

          return (
            <article
              key={solution.id}
              onClick={() => onArticleClick(solution.id)}
              className={`p-5 hover:bg-muted/50 transition-colors cursor-pointer ${
                isAnnouncementItem ? 'bg-amber-50/50' : ''
              }`}
            >
              {/* ID badge */}
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 text-xs font-mono bg-muted text-muted-foreground rounded">
                  #{solution.id}
                </span>
              </div>

              {/* Title row */}
              <div className="flex items-start gap-2 mb-2">
                {solution.is_pinned && (
                  <Pin className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                )}
                {isAnnouncementItem && (
                  <Megaphone className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                )}
                <h3 className={`font-medium flex-1 ${isAnnouncementItem ? 'text-amber-800' : 'text-foreground'}`}>
                  {solution.title}
                </h3>
              </div>

              {/* Meta row */}
              <div className={`flex items-center justify-between text-sm ${
                isAnnouncementItem ? 'text-amber-600' : 'text-muted-foreground'
              }`}>
                <span>{solution.username}</span>
                <div className="flex items-center gap-4">
                  {onLike && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onLike(solution.id)
                      }}
                      className="flex items-center gap-1 hover:text-red-500 transition-colors"
                    >
                      <Heart className="w-4 h-4" />
                      {solution.like_count}
                    </button>
                  )}
                  {!onLike && (
                    <span className="flex items-center gap-1">
                      <Heart className="w-4 h-4" />
                      {solution.like_count}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {solution.view_count}
                  </span>
                  <span>{formatTime(solution.created_at)}</span>
                  {currentUserId === solution.user_id && onDelete && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onDelete(solution.id)
                      }}
                      className="flex items-center gap-1 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </div>
  )
}
