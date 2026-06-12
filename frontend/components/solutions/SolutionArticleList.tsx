'use client'

import { useMemo } from 'react'
import { Eye, Heart, Pin, Megaphone, Trash2, Inbox } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Panel } from '@/components/layout'
import { EmptyState } from '@/components/layout'
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
      <Panel>
        <div className="p-8 flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">{t('加载中...', 'Loading...')}</div>
        </div>
      </Panel>
    )
  }

  if (filteredSolutions.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        title={t('暂无内容', 'No content yet')}
        description={t('该分类下还没有题解', 'No solutions in this category')}
      />
    )
  }

  return (
    <Panel>
      <div className="divide-y divide-border">
        {filteredSolutions.map(solution => {
          const isAnnouncementItem = solution.is_announcement

          return (
            <article
              key={solution.id}
              className={`relative px-6 py-4 hover:bg-muted/30 ${
                isAnnouncementItem ? 'bg-muted/30' : ''
              }`}
            >
              <Button
                type="button"
                variant="ghost"
                onClick={() => onArticleClick(solution.id)}
                className="absolute inset-0 z-0 h-full w-full"
                aria-label={t(`打开题解：${solution.title}`, `Open solution: ${solution.title}`)}
              />
              <div className="relative z-10 flex items-start gap-2 mb-2 pointer-events-none">
                <span className="px-2 py-0.5 text-xs font-mono bg-muted text-muted-foreground">
                  #{solution.id}
                </span>
              </div>

              <div className="relative z-10 flex items-start gap-2 mb-2 pointer-events-none">
                {solution.is_pinned && (
                  <Pin className="size-4 text-foreground flex-shrink-0 mt-0.5" strokeWidth={1.5} />
                )}
                {isAnnouncementItem && (
                  <Megaphone className="size-4 text-foreground flex-shrink-0 mt-0.5" strokeWidth={1.5} />
                )}
                <h3 className={`font-medium flex-1 ${isAnnouncementItem ? 'text-foreground' : 'text-foreground'}`}>
                  {solution.title}
                </h3>
              </div>

              <div className="relative z-10 flex items-center justify-between text-sm text-muted-foreground pointer-events-none">
                <span>{solution.username}</span>
                <div className="flex items-center gap-4">
                  {onLike ? (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        onLike(solution.id)
                      }}
                      className="flex items-center gap-1 hover:text-red-500"
                    >
                      <Heart className="size-4" strokeWidth={1.5} />
                      {solution.like_count}
                    </button>
                  ) : (
                    <span className="flex items-center gap-1">
                      <Heart className="size-4" strokeWidth={1.5} />
                      {solution.like_count}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Eye className="size-4" strokeWidth={1.5} />
                    {solution.view_count}
                  </span>
                  <span>{formatTime(solution.created_at)}</span>
                  {currentUserId === solution.user_id && onDelete && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation()
                        onDelete(solution.id)
                      }}
                      className="size-7 hover:text-red-500"
                      aria-label={t('删除题解', 'Delete solution')}
                    >
                      <Trash2 className="size-4" strokeWidth={1.5} />
                    </Button>
                  )}
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </Panel>
  )
}
