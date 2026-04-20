'use client'

import { useState, useEffect } from 'react'
import { MessageSquare, Pin, Eye, Heart, Plus, X, Trash, Megaphone } from 'lucide-react'
import { getSolutionSummary, createSolution, likeSolution, deleteSolution, SolutionSummary, SolutionCreate } from '@/lib/api/solutions'
import { getStoredToken, getStoredUser } from '@/lib/api/auth'

type TabType = 'hot' | 'new' | 'pinned' | 'announcement'

interface SolutionBoardProps {
  lang?: 'zh' | 'en'
  compact?: boolean
}

export function SolutionBoard({ lang = 'zh', compact = false }: SolutionBoardProps) {
  const [activeTab, setActiveTab] = useState<TabType>('hot')
  const [solutions, setSolutions] = useState<SolutionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [showEditor, setShowEditor] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newContent, setNewContent] = useState('')
  const [isAnnouncement, setIsAnnouncement] = useState(false)
  const [submitting, setSubmitting] = useState(false)
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
    try {
      const token = getStoredToken()
      if (!token) {
        setLoading(false)
        return
      }
      const data = await getSolutionSummary(token, 50)
      setSolutions(data)
    } catch (e) {
      console.error('Failed to fetch solutions:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newTitle.trim()) return
    const token = getStoredToken()
    if (!token) {
      alert(lang === 'zh' ? '请先登录' : 'Please login first')
      return
    }
    setSubmitting(true)
    try {
      await createSolution(token, {
        title: newTitle.trim(),
        content: newContent.trim(),
        is_announcement: isAnnouncement,
      })
      setNewTitle('')
      setNewContent('')
      setIsAnnouncement(false)
      setShowEditor(false)
      fetchSolutions()
    } catch (e) {
      console.error('Failed to create solution:', e)
    } finally {
      setSubmitting(false)
    }
  }

  const handleLike = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const token = getStoredToken()
    if (!token) return
    try {
      const updated = await likeSolution(token, id)
      setSolutions(prev => prev.map(s => s.id === id ? { ...s, like_count: updated.like_count } : s))
    } catch (e) {
      console.error('Failed to like:', e)
    }
  }

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const token = getStoredToken()
    if (!token) return
    if (!confirm(lang === 'zh' ? '确定删除这条题解吗？' : 'Delete this solution?')) return
    try {
      await deleteSolution(token, id)
      setSolutions(prev => prev.filter(s => s.id !== id))
    } catch (e) {
      console.error('Failed to delete:', e)
    }
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
    return date.toLocaleDateString()
  }

  const getSortedSolutions = () => {
    let filtered = [...solutions]

    // Filter by tab
    if (activeTab === 'announcement') {
      filtered = filtered.filter(s => s.is_announcement)
    } else if (activeTab === 'pinned') {
      filtered = filtered.filter(s => s.is_pinned)
    } else {
      // Exclude announcements from hot/new tabs unless they're also pinned
      if (activeTab !== 'pinned') {
        // Keep all, but announcements will be shown at top
      }
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
        className={`group p-3 rounded-xl hover:bg-muted transition-colors cursor-pointer ${
          isAnnouncementItem ? 'bg-amber-50/50 border border-amber-200 hover:bg-amber-100/50' : 'bg-muted/50'
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
          <h4 className={`font-medium text-sm flex-1 line-clamp-2 ${isAnnouncementItem ? 'text-amber-800' : 'text-foreground'}`}>
            {solution.title}
          </h4>
        </div>

        {/* Meta row */}
        <div className={`flex items-center justify-between mt-2 text-xs ${
          isAnnouncementItem ? 'text-amber-600' : 'text-muted-foreground'
        }`}>
          <span>{solution.username}</span>
          <div className="flex items-center gap-3">
            {currentUserId === solution.user_id && (
              <button
                onClick={(e) => handleDelete(solution.id, e)}
                className="flex items-center gap-1 hover:text-red-500 transition-colors"
              >
                <Trash className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={(e) => handleLike(solution.id, e)}
              className="flex items-center gap-1 hover:text-red-500 transition-colors"
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
          {t('题解广场', 'Solutions')}
        </h3>
        <button
          onClick={() => setShowEditor(true)}
          className="flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t('发布', 'Post')}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4 flex-shrink-0">
        {(Object.keys(tabMap) as TabType[]).map(tab => (
          <button
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

      {/* Editor Modal */}
      {showEditor && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-2xl border border-border w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-foreground">{t('发布内容', 'Post Content')}</h3>
              <button
                onClick={() => setShowEditor(false)}
                className="p-1 hover:bg-muted rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Announcement toggle - admin only */}
              {isAdmin && (
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAnnouncement}
                    onChange={e => setIsAnnouncement(e.target.checked)}
                    className="w-4 h-4 rounded border-amber-400 text-amber-500 focus:ring-amber-500"
                  />
                  <Megaphone className="w-4 h-4 text-amber-500" />
                  <span className="text-sm text-foreground">{t('发布为公告', 'Post as Announcement')}</span>
                </label>
              )}

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  {t('标题', 'Title')} *
                </label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  placeholder={isAnnouncement ? t('输入公告标题...', 'Enter announcement title...') : t('输入题解标题...', 'Enter solution title...')}
                  className="w-full px-3 py-2 bg-muted rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  maxLength={200}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  {t('内容', 'Content')}
                </label>
                <textarea
                  value={newContent}
                  onChange={e => setNewContent(e.target.value)}
                  placeholder={t('详细描述...', 'Describe in detail...')}
                  className="w-full px-3 py-2 bg-muted rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  rows={6}
                />
              </div>

              <button
                onClick={handleCreate}
                disabled={!newTitle.trim() || submitting}
                className="w-full py-2.5 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? t('发布中...', 'Posting...') : t('发布', 'Post')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
