'use client'

import { Suspense, useEffect, useState, useMemo } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { MessageSquare, Plus, ArrowLeft, Home, Search } from 'lucide-react'
import { getSolutionSummary, createSolution, deleteSolution, likeSolution, SolutionSummary, SolutionCreate, SolutionUpdate } from '@/lib/api/solutions'
import { getStoredToken, getStoredUser, User } from '@/lib/api/auth'
import { SolutionCategoryNav } from '@/components/solutions/SolutionCategoryNav'
import { SolutionArticleList } from '@/components/solutions/SolutionArticleList'
import { SolutionEditor } from '@/components/solutions/SolutionEditor'

type CategoryType = 'hot' | 'new' | 'pinned' | 'announcement'
type PageMode = 'list' | 'create'

function SolutionsContent() {
  const { push } = useRouter()
  const searchParams = useSearchParams()

  const [solutions, setSolutions] = useState<SolutionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const [pageMode, setPageMode] = useState<PageMode>('list')
  const [lang, setLang] = useState<'zh' | 'en'>('zh')
  const [searchQuery, setSearchQuery] = useState('')

  const activeCategory = (searchParams.get('tab') as CategoryType) || 'hot'

  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  const filteredSolutions = useMemo(() => {
    if (!searchQuery.trim()) return solutions

    const query = searchQuery.toLowerCase().trim()
    const queryNum = parseInt(query)

    return solutions.filter(s => {
      // Match by ID (exact number match)
      if (queryNum && s.id === queryNum) return true
      // Match by title keyword
      if (s.title.toLowerCase().includes(query)) return true
      // Match by problem link containing the number
      return false
    })
  }, [solutions, searchQuery])

  useEffect(() => {
    const user = getStoredUser()
    const token = getStoredToken()

    if (!token || !user) {
      push('/login')
      return
    }

    setCurrentUser(user)
    setIsAdmin(user.is_admin || false)

    const savedLang = localStorage.getItem('language') || 'zh'
    setLang(savedLang as 'zh' | 'en')

    fetchSolutions(token)
  }, [activeCategory])

  const fetchSolutions = async (token: string) => {
    try {
      setLoading(true)
      const data = await getSolutionSummary(token, 50)
      setSolutions(data)
    } catch (error) {
      console.error('Failed to fetch solutions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryChange = (category: CategoryType) => {
    push(`/solutions?tab=${category}`)
  }

  const handleArticleClick = (id: number) => {
    push(`/solutions/${id}`)
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('确定删除这篇题解吗？', 'Delete this solution?'))) return

    const token = getStoredToken()
    if (!token) return

    try {
      await deleteSolution(token, id)
      fetchSolutions(token)
    } catch (error) {
      console.error('Failed to delete:', error)
    }
  }

  const handleLike = async (id: number) => {
    const token = getStoredToken()
    if (!token) return

    try {
      const updated = await likeSolution(token, id)
      setSolutions(prev => prev.map(s => s.id === id ? { ...s, like_count: updated.like_count } : s))
    } catch (error) {
      console.error('Failed to like:', error)
    }
  }

  const handleSave = async (data: SolutionCreate | SolutionUpdate) => {
    const token = getStoredToken()
    if (!token) return
    // Force title to be string (editor requires title)
    const solutionData = data as SolutionCreate
    await createSolution(token, solutionData)
    setPageMode('list')
    fetchSolutions(token)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            {pageMode === 'create' ? (
              <>
                <button type="button"
                  onClick={() => setPageMode('list')}
                  className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <ArrowLeft className="size-5" />
                  <span>{t('取消发布', 'Cancel')}</span>
                </button>
                <h2 className="text-lg font-semibold">{t('发布题解', 'New Solution')}</h2>
                <div className="w-24" />
              </>
            ) : (
              <>
                <div className="flex items-center gap-4">
                  <button type="button"
                    onClick={() => push('/dashboard')}
                    className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
                    title={t('返回首页', 'Go to Dashboard')}
                  >
                    <Home className="size-5" />
                  </button>
                  <MessageSquare className="size-6 text-primary" />
                  <h1 className="text-lg font-semibold">{t('讨论区', 'Discussion')}</h1>
                </div>
                <button type="button"
                  onClick={() => setPageMode('create')}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors"
                >
                  <Plus className="size-4" />
                  {t('发布', 'Post')}
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1400px] mx-auto px-4 sm:p-6">
        {pageMode === 'create' ? (
          <SolutionEditor
            onSave={handleSave}
            onCancel={() => setPageMode('list')}
            isAdmin={isAdmin}
            lang={lang}
            isFullPage
          />
        ) : (
          <div className="flex gap-6">
            {/* Left: Category Navigation */}
            <aside className="w-48 flex-shrink-0">
              <SolutionCategoryNav
                activeCategory={activeCategory}
                onCategoryChange={handleCategoryChange}
                lang={lang}
              />
            </aside>

            {/* Right: Article List */}
            <section className="flex-1 min-w-0">
              {/* Search bar */}
              <div className="mb-4 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-5 text-muted-foreground" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t('搜索题解序号或关键词', 'Search by ID or keyword')}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-colors"
                />
                {searchQuery && (
                  <button type="button"
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    ×
                  </button>
                )}
              </div>

              {searchQuery && (
                <div className="mb-3 text-sm text-muted-foreground">
                  {t(`找到 ${filteredSolutions.length} 个结果`, `${filteredSolutions.length} results found`)}
                </div>
              )}

              <SolutionArticleList
                solutions={searchQuery ? filteredSolutions : solutions}
                loading={loading}
                activeCategory={activeCategory}
                onArticleClick={handleArticleClick}
                onDelete={handleDelete}
                onLike={handleLike}
                currentUserId={currentUser?.id}
                lang={lang}
              />
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default function SolutionsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent"></div>
      </div>
    }>
      <SolutionsContent />
    </Suspense>
  )
}
