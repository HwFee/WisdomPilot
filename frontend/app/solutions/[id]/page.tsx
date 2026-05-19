'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Edit3, Trash2, Heart, Eye, Pin, Megaphone, Home } from 'lucide-react'
import { getSolution, deleteSolution, updateSolution, SolutionResponse, SolutionUpdate } from '@/lib/api/solutions'
import { getStoredToken, getStoredUser, User } from '@/lib/api/auth'
import { SolutionMarkdown } from '@/components/solutions/SolutionMarkdown'
import { SolutionEditor } from '@/components/solutions/SolutionEditor'

type EditMode = 'view' | 'edit'

export default function SolutionDetailPage() {
  const params = useParams()
  const { push } = useRouter()
  const solutionId = parseInt(params.id as string)

  const [solution, setSolution] = useState<SolutionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [userState, setUserState] = useState<{ currentUser: User | null; isAdmin: boolean; lang: 'zh' | 'en' }>({
    currentUser: null,
    isAdmin: false,
    lang: 'zh',
  })
  const [editMode, setEditMode] = useState<EditMode>('view')
  const { currentUser, isAdmin, lang } = userState

  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  useEffect(() => {
    const user = getStoredUser()
    const token = getStoredToken()

    if (!token || !user) {
      push('/login')
      return
    }

    const savedLang = localStorage.getItem('language') || 'zh'
    setUserState({
      currentUser: user,
      isAdmin: user.is_admin || false,
      lang: savedLang as 'zh' | 'en',
    })
  }, [push])

  useEffect(() => {
    const token = getStoredToken()
    if (!token) return
    fetchSolution(token)
  }, [solutionId])

  const fetchSolution = async (token: string) => {
    try {
      setLoading(true)
      const data = await getSolution(token, solutionId)
      setSolution(data)
    } catch (error) {
      console.error('Failed to fetch solution:', error)
      push('/solutions')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(t('确定删除这篇题解吗？', 'Delete this solution?'))) return

    const token = getStoredToken()
    if (!token) return

    try {
      await deleteSolution(token, solutionId)
      push('/solutions')
    } catch (error) {
      console.error('Failed to delete:', error)
    }
  }

  const handleEditSave = async (data: SolutionUpdate & { is_announcement?: boolean }) => {
    const token = getStoredToken()
    if (!token) return

    try {
      await updateSolution(token, solutionId, data)
      setEditMode('view')
      fetchSolution(token)
    } catch (error) {
      console.error('Failed to update:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">{t('加载中...', 'Loading...')}</div>
      </div>
    )
  }

  if (!solution) return null

  const isOwner = currentUser?.id === solution.user_id

  // Full page editor mode
  if (editMode === 'edit') {
    return (
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
          <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
            <div className="flex items-center justify-between h-16">
              <button type="button"
                onClick={() => setEditMode('view')}
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="size-5" />
                <span>{t('取消编辑', 'Cancel Edit')}</span>
              </button>
              <h2 className="text-lg font-semibold">{t('编辑题解', 'Edit Solution')}</h2>
              <div className="w-24" /> {/* Spacer for centering */}
            </div>
          </div>
        </header>
        <main className="max-w-[1400px] mx-auto px-4 sm:p-6">
          <SolutionEditor
            initialTitle={solution.title}
            initialContent={solution.content}
            initialIsAnnouncement={solution.is_announcement}
            onSave={handleEditSave}
            onCancel={() => setEditMode('view')}
            isAdmin={isAdmin}
            lang={lang}
            isFullPage
          />
        </main>
      </div>
    )
  }

  // View mode
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
        <div className="max-w-[1000px] mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button type="button"
                onClick={() => push('/dashboard')}
                className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                title={t('返回首页', 'Go to Dashboard')}
              >
                <Home className="size-5" />
              </button>
              <button type="button"
                onClick={() => push('/solutions')}
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="size-5" />
                <span>{t('返回列表', 'Back')}</span>
              </button>
            </div>

            {isOwner && (
              <div className="flex items-center gap-2">
                <button type="button"
                  onClick={() => setEditMode('edit')}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-muted rounded-lg hover:bg-muted/80 transition-colors"
                >
                  <Edit3 className="size-4" />
                  {t('编辑', 'Edit')}
                </button>
                <button type="button"
                  onClick={handleDelete}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-red-500 bg-red-500/10 rounded-lg hover:bg-red-500/20 transition-colors"
                >
                  <Trash2 className="size-4" />
                  {t('删除', 'Delete')}
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-[1000px] mx-auto px-4 sm:px-6 py-8">
        <article className="bg-card rounded-2xl border border-border p-8">
          {/* Title & Meta */}
          <header className="mb-8">
            <div className="flex items-start gap-3 mb-4">
              {solution.is_pinned && <Pin className="size-5 text-primary flex-shrink-0 mt-1" />}
              {solution.is_announcement && <Megaphone className="size-5 text-amber-500 flex-shrink-0 mt-1" />}
              <h1 className={`text-2xl font-semibold ${solution.is_announcement ? 'text-amber-800' : 'text-foreground'}`}>
                {solution.title}
              </h1>
            </div>

            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>{solution.username}</span>
              <span suppressHydrationWarning>{new Date(solution.created_at).toLocaleDateString()}</span>
              <span className="flex items-center gap-1">
                <Eye className="size-4" />
                {solution.view_count}
              </span>
              <span className="flex items-center gap-1">
                <Heart className="size-4" />
                {solution.like_count}
              </span>
            </div>
          </header>

          {/* Markdown Content */}
          <div className="markdown-body">
            <SolutionMarkdown content={solution.content} />
          </div>

          {/* Tags */}
          {solution.tags && solution.tags.length > 0 && (
            <footer className="mt-8 pt-6 border-t">
              <div className="flex flex-wrap gap-2">
                {solution.tags.map(tag => (
                  <span key={tag} className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            </footer>
          )}
        </article>
      </main>
    </div>
  )
}
