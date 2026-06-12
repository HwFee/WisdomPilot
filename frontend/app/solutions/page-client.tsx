'use client'

import { Suspense, useState, useMemo } from 'react'
import { useSearchParams } from 'next/navigation'
import { MessageSquare, Plus, ArrowLeft, Home, Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SolutionCategoryNav } from '@/components/solutions/SolutionCategoryNav'
import { SolutionArticleList } from '@/components/solutions/SolutionArticleList'
import { SolutionEditor } from '@/components/solutions/SolutionEditor'
import { useSolutionsData } from './hooks/use-solutions-data'
import { filterSolutions } from './lib/solutions-utils'
import type { CategoryType, PageMode } from './lib/solutions-utils'
import type { SolutionCreate, SolutionUpdate } from '@/lib/api/solutions'

function SolutionsContent() {
  const searchParams = useSearchParams()
  const {
    solutions,
    loading,
    userState,
    handleDelete,
    handleLike,
    handleSave,
    push,
  } = useSolutionsData()

  const [pageMode, setPageMode] = useState<PageMode>('list')
  const [searchQuery, setSearchQuery] = useState('')
  const { currentUser, isAdmin, lang } = userState

  const activeCategory = (searchParams.get('tab') as CategoryType) || 'hot'

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const filteredSolutions = useMemo(
    () => filterSolutions(solutions, searchQuery),
    [solutions, searchQuery],
  )

  const handleCategoryChange = (category: CategoryType) => {
    push(`/solutions?tab=${category}`)
  }

  const handleArticleClick = (id: number) => {
    push(`/solutions/${id}`)
  }

  const handleSaveWrapper = async (data: SolutionCreate | SolutionUpdate) => {
    await handleSave(data, () => setPageMode('list'))
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            {pageMode === 'create' ? (
              <>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setPageMode('list')}
                >
                  <ArrowLeft className="size-5 mr-2" strokeWidth={1.5} />
                  {t('取消发布', 'Cancel')}
                </Button>
                <h2 className="text-lg font-semibold">{t('发布题解', 'New Solution')}</h2>
                <div className="w-24" />
              </>
            ) : (
              <>
                <div className="flex items-center gap-4">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => push('/dashboard')}
                    title={t('返回首页', 'Go to Dashboard')}
                    aria-label={t('返回首页', 'Go to Dashboard')}
                  >
                    <Home className="size-5" />
                  </Button>
                  <MessageSquare className="size-6 text-primary" />
                  <h1 className="text-lg font-semibold">{t('讨论区', 'Discussion')}</h1>
                </div>
                <Button
                  type="button"
                  onClick={() => setPageMode('create')}
                >
                  <Plus className="size-4 mr-2" strokeWidth={1.5} />
                  {t('发布', 'Post')}
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1400px] mx-auto px-4 sm:p-6">
        {pageMode === 'create' ? (
          <SolutionEditor
            onSave={handleSaveWrapper}
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
                  aria-label={t('搜索题解', 'Search solutions')}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-colors"
                />
                {searchQuery && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 size-8"
                    aria-label={t('清除搜索', 'Clear search')}
                  >
                    <X className="size-4" />
                  </Button>
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
                onDelete={(id) => handleDelete(id, t('确定删除这篇题解吗？', 'Delete this solution?'))}
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

export default function SolutionsClient() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent" />
      </div>
    }>
      <SolutionsContent />
    </Suspense>
  )
}
