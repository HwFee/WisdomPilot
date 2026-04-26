'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { MessageSquare, Pin, Eye, Heart, ArrowRight, Megaphone, AlertCircle } from 'lucide-react'
import { getSolutionSummary, likeSolution, SolutionSummary } from '@/lib/api/solutions'
import { getStoredToken, getStoredUser } from '@/lib/api/auth'

type TabType = 'hot' | 'new' | 'pinned' | 'announcement'

interface SolutionBoardProps {
  lang?: 'zh' | 'en'
  compact?: boolean
}

export function SolutionBoard({ lang = 'zh', compact = false }: SolutionBoardProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<TabType>('hot')
  const [solutions, setSolutions] = useState<SolutionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const [isAdmin, setIsAdmin] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const tabMap: Record<TabType, string> = {
    hot: t('最热', 'Hot'),
    new: t('最新', 'New'),
    pinned: t('置顶', 'Pinned'),
    announcement: t('公告', 'Announcement'),
  }

  useEffect(() => {
    const user = getStoredUser()
    if (user) {
      setCurrentUserId(user.id)
      setIsAdmin(user.is_admin || false)
    }
    fetchSolutions()
  }, [])

  const fetchSolutions = async () => {
    setError(null)
    try {
      const token = getStoredToken()
      if (!token) {
        setLoading(false)
        return
      }
      const data = await getSolutionSummary(token, 50)
      setSolutions(data)
    } catch (e) {
      const msg = e instanceof Error ? e.message : t('加载失败', 'Failed to load')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

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
    router.push(`/solutions/${id}`)
  }

  const handleEnterSolutions = () => {
    router.push('/solutions')
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(hours / 24)

    if (hours < 1) return t('刚刚', 'Just now')
    if (hours < 24) return `${hours}${t('小时前', 'h ago')}`
    if (days < 7) return `${days}${t('天前', 'd ago')}`
    return date.toLocaleDateString('zh-CN')
  }

  const getSortedSolutions = () => {
    let filtered = [...solutions]

    // Filter by tab
    if (activeTab === 'announcement') {
      filtered = filtered.filter(s => s.is_announcement)
    } else if (activeTab === 'pinned') {
      filtered = filtered.filter(s => s.is_pinned)
    }

    // Sort: announcements first (if not in announcement tab), then pinned, then by sort type
    filtered.sort((a, b) => {
      // Announcements always at top (unless in announcement tab)
      if (activeTab !== 'announcement') {
        if (a.is_announcement && !b.is_announcement) return -1
        if (!a.is_announcement && b.is_announcement) return 1
      }
      // Then pinned
      if (a.is_pinned && !b.is_pinned) return -1
      if (!a.is_pinned && b.is_pinned) return 1
      // Then by sort type
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
        onClick={() => handleItemClick(solution.id)}
        className={`group p-3 rounded-xl hover:bg-muted transition-colors cursor-pointer ${
          isAnnouncementItem ? 'bg-amber-50/50 border border-amber-200 hover:bg-amber-100/50 dark:bg-amber-950/20 dark:border-amber-800' : 'bg-muted/50'
        }`}
      >
        {/* Title row with indicators */}
        <div className="flex items-start gap-2">
          {solution.is_pinned && (
            <Pin className="w-3.5 h-3.5 text-primary flex-shrink-0 mt-0.5" />
          )}
          {isAnnouncementItem && (
            <Megaphone className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
          )}
          <h4 className={`font-medium text-sm flex-1 line-clamp-2 ${isAnnouncementItem ? 'text-amber-800 dark:text-amber-300' : 'text-foreground'}`}>
            {solution.title}
          </h4>
        </div>

        {/* Meta row */}
        <div className={`flex items-center justify-between mt-2 text-xs ${
          isAnnouncementItem ? 'text-amber-600 dark:text-amber-400' : 'text-muted-foreground'
        }`}>
          <span>{solution.username}</span>
          <div className="flex items-center gap-3">
            <button type="button"
              onClick={(e) => handleLike(solution.id, e)}
              className="flex items-center gap-1 hover:text-red-500 transition-colors"
              title={t('点赞', 'Like')}
            >
              <Heart className="w-3.5 h-3.5" />
              {solution.like_count}
            </button>
            <span className="flex items-center gap-1">
              <Eye className="w-3.5 h-3.5" />
              {solution.view_count}
            </span>
            <span>{formatTime(solution.created_at)}</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card rounded-2xl border border-border p-6 h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <h3 className="font-semibold text-foreground flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-primary" />
          {t('讨论区', 'Discussion')}
        </h3>
        <button type="button"
          onClick={handleEnterSolutions}
          className="flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors"
        >
          {t('进入', 'Enter')}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4 flex-shrink-0">
        {(Object.keys(tabMap) as TabType[]).map(tab => (
          <button type="button"
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {tabMap[tab]}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <span className="animate-pulse">{t('加载中...', 'Loading...')}</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full text-destructive">
            <AlertCircle className="w-10 h-10 mb-2" />
            <p className="text-sm mb-3">{error}</p>
            <button type="button"
              onClick={fetchSolutions}
              className="px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 transition-colors"
            >
              {t('重试', 'Retry')}
            </button>
          </div>
        ) : getSortedSolutions().length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <MessageSquare className="w-10 h-10 mb-2 opacity-50" />
            <p className="text-sm">{t('暂无内容', 'No content yet')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {getSortedSolutions().map(renderSolutionItem)}
          </div>
        )}
      </div>
    </div>
  )
}
