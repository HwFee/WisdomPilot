'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { MessageSquare, Pin, Eye, Heart, ArrowRight, Megaphone, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Panel, PanelHeader } from '@/components/layout'
import { getSolutionSummary, likeSolution, SolutionSummary } from '@/lib/api/solutions'
import { getStoredToken } from '@/lib/api/auth'

type TabType = 'hot' | 'new' | 'pinned' | 'announcement'

const SOLUTION_FETCH_LIMIT = 50
const MS_PER_HOUR = 1000 * 60 * 60

const TIME_THRESHOLDS = {
  HOUR: 1,
  DAY: 24,
  WEEK: 7,
} as const

interface SolutionBoardProps {
  lang?: 'zh' | 'en'
}

export function SolutionBoard({ lang = 'zh' }: SolutionBoardProps) {
  const { push } = useRouter()
  const [activeTab, setActiveTab] = useState<TabType>('hot')
  const [solutions, setSolutions] = useState<SolutionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const tabMap: Record<TabType, string> = {
    hot: t('最热', 'Hot'),
    new: t('最新', 'New'),
    pinned: t('置顶', 'Pinned'),
    announcement: t('公告', 'Announcement'),
  }

  const fetchSolutions = useCallback(async () => {
    setError(null)
    try {
      const token = getStoredToken()
      if (!token) {
        setLoading(false)
        return
      }
      const data = await getSolutionSummary(token, SOLUTION_FETCH_LIMIT)
      setSolutions(data)
    } catch (e) {
      const msg = e instanceof Error ? e.message : (lang === 'zh' ? '加载失败' : 'Failed to load')
      /* react-doctor-disable-next-line no-derived-state */
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [lang])

  useEffect(() => {
    // react-doctor-disable-next-line no-derived-state, react-doctor/no-derived-state — error is fetched from async API, not derivable from props/state
    fetchSolutions()
  }, [fetchSolutions])

  const handleLike = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const token = getStoredToken()
    if (!token) {
      alert(t('请先登录', 'Please login first'))
      return
    }
    try {
      const updated = await likeSolution(token, id)
      setSolutions(prev => prev.map(s => s.id === id ? { ...s, like_count: updated.like_count } : s))
    } catch (e) {
      const msg = e instanceof Error ? e.message : t('点赞失败', 'Failed to like')
      alert(msg)
    }
  }

  const handleItemClick = (id: number) => {
    push(`/solutions/${id}`)
  }

  const handleEnterSolutions = () => {
    push('/solutions')
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / MS_PER_HOUR)
    const days = Math.floor(hours / 24)

    if (hours < TIME_THRESHOLDS.HOUR) return t('刚刚', 'Just now')
    if (hours < TIME_THRESHOLDS.DAY) return `${hours}${t('小时前', 'h ago')}`
    if (days < TIME_THRESHOLDS.WEEK) return `${days}${t('天前', 'd ago')}`
    return date.toLocaleDateString('zh-CN')
  }

  const getSortedSolutions = () => {
    let filtered = [...solutions]

    if (activeTab === 'announcement') {
      filtered = filtered.filter(s => s.is_announcement)
    } else if (activeTab === 'pinned') {
      filtered = filtered.filter(s => s.is_pinned)
    }

    filtered.sort((a, b) => {
      if (activeTab !== 'announcement') {
        if (a.is_announcement && !b.is_announcement) return -1
        if (!a.is_announcement && b.is_announcement) return 1
      }
      if (a.is_pinned && !b.is_pinned) return -1
      if (!a.is_pinned && b.is_pinned) return 1
      if (activeTab === 'hot') return b.hot_score - a.hot_score
      if (activeTab === 'new' || activeTab === 'announcement') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }
      return 0
    })
    return filtered
  }

  const renderSolutionItem = (solution: SolutionSummary) => {
    const isAnnouncementItem = solution.is_announcement

    return (
      <div
        key={solution.id}
        className={`relative group px-8 py-4 hover:bg-muted transition-colors ${
          isAnnouncementItem
            ? 'bg-amber-50 hover:bg-amber-100 dark:bg-amber-950 dark:hover:bg-amber-900'
            : ''
        }`}
      >
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => handleItemClick(solution.id)}
          className="absolute inset-0 z-0 h-full w-full rounded-none p-0"
          aria-label={t(`查看题解：${solution.title}`, `View solution: ${solution.title}`)}
        />
        <div className="flex items-start gap-2">
          {solution.is_pinned && (
            <Pin className="size-3.5 text-primary flex-shrink-0 mt-0.5" strokeWidth={1.5} />
          )}
          {isAnnouncementItem && (
            <Megaphone className="size-3.5 text-amber-500 flex-shrink-0 mt-0.5" strokeWidth={1.5} />
          )}
          <h4 className={`font-medium text-sm flex-1 line-clamp-2 ${isAnnouncementItem ? 'text-amber-800 dark:text-amber-300' : 'text-foreground'}`}>
            {solution.title}
          </h4>
        </div>

        <div className={`flex items-center justify-between mt-2 text-xs ${
          isAnnouncementItem ? 'text-amber-600 dark:text-amber-400' : 'text-muted-foreground'
        }`}>
          <span>{solution.username}</span>
          <div className="flex items-center gap-3">
            <Button type="button"
              variant="ghost"
              size="sm"
              onClick={(e) => handleLike(solution.id, e)}
              className="relative z-10 h-auto p-1 px-2 text-xs hover:text-red-500"
              title={t('点赞', 'Like')}
            >
              <Heart className="size-3.5" strokeWidth={1.5} />
              {solution.like_count}
            </Button>
            <span className="flex items-center gap-1">
              <Eye className="size-3.5" strokeWidth={1.5} />
              {solution.view_count}
            </span>
            <span>{formatTime(solution.created_at)}</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Panel className="h-full flex flex-col">
      <PanelHeader
        title={t('题解广场', 'Solutions')}
        count={t(`${solutions.length} 篇`, `${solutions.length}`)}
        action={
          <Button type="button"
            variant="secondary"
            size="sm"
            onClick={handleEnterSolutions}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            {t('进入', 'Enter')}
            <ArrowRight className="size-4" strokeWidth={1.5} />
          </Button>
        }
      />

      <div className="flex gap-2 px-8 py-4 border-b border-border flex-shrink-0">
        {(Object.keys(tabMap) as TabType[]).map(tab => (
          <Button type="button"
            variant={activeTab === tab ? "default" : "ghost"}
            size="sm"
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              activeTab === tab
                ? ''
                : 'bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {tabMap[tab]}
          </Button>
        ))}
      </div>

      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <span className="animate-pulse">{t('加载中...', 'Loading...')}</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full text-destructive">
            <AlertCircle className="size-10 mb-2" strokeWidth={1.5} />
            <p className="text-sm mb-3">{error}</p>
            <Button type="button"
              variant="secondary"
              size="sm"
              onClick={fetchSolutions}
              className="px-3 py-1.5 rounded-lg text-sm hover:bg-secondary"
            >
              {t('重试', 'Retry')}
            </Button>
          </div>
        ) : getSortedSolutions().length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <MessageSquare className="size-10 mb-2 opacity-50" strokeWidth={1.5} />
            <p className="text-sm">{t('暂无内容', 'No content yet')}</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {getSortedSolutions().map(renderSolutionItem)}
          </div>
        )}
      </div>
    </Panel>
  )
}
