'use client'

import { Suspense, useState, useMemo } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { MessageSquare, Plus, ArrowLeft, Home, Search, X, Inbox } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageContainer, EmptyState } from '@/components/layout'
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
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          {pageMode === 'create' ? (
            <>
              <Button variant="ghost" onClick={() => setPageMode('list')}>
                <ArrowLeft className="size-5 mr-2" strokeWidth={1.5} />
                {t('取消发布', 'Cancel')}
              </Button>
              <h1 className="text-sm font-semibold uppercase tracking-[2px] ml-4">
                {t('发布题解', 'New Solution')}
              </h1>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="icon" aria-label="返回首页">
                <Link href="/dashboard">
                  <Home className="size-5" strokeWidth={1.5} />
                </Link>
              </Button>
              <MessageSquare className="size-5 text-foreground" strokeWidth={1.5} />
              <h1 className="text-sm font-semibold uppercase tracking-[2px]">
                {t('题解讨论', 'Discussion')}
              </h1>
              <div className="ml-auto flex items-center gap-2">
                <Button onClick={() => setPageMode('create')}>
                  <Plus className="size-4 mr-2" strokeWidth={1.5} />
                  {t('发布', 'Post')}
                </Button>
              </div>
            </>
          )}
        </div>
      </header>

      <main className="bg-background min-h-[calc(100vh-3.5rem)]">
        <PageContainer className="py-8">
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
              <aside className="w-48 flex-shrink-0">
                <SolutionCategoryNav
                  activeCategory={activeCategory}
                  onCategoryChange={handleCategoryChange}
                  lang={lang}
                />
              </aside>

              <section className="flex-1 min-w-0 space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" strokeWidth={1.5} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t('搜索题解序号或关键词', 'Search by ID or keyword')}
                    aria-label={t('搜索题解', 'Search solutions')}
                    className="w-full h-10 pl-10 pr-4 bg-background border border-border text-sm focus:outline-none focus:border-foreground"
                  />
                  {searchQuery && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setSearchQuery('')}
                      className="absolute right-1 top-1/2 -translate-y-1/2 size-8"
                      aria-label={t('清除搜索', 'Clear search')}
                    >
                      <X className="size-4" strokeWidth={1.5} />
                    </Button>
                  )}
                </div>

                {searchQuery && (
                  <div className="text-sm text-muted-foreground">
                    {t(`找到 ${filteredSolutions.length} 个结果`, `${filteredSolutions.length} results found`)}
                  </div>
                )}

                {!searchQuery && solutions.length === 0 && !loading ? (
                  <EmptyState
                    icon={Inbox}
                    title={t('暂无题解', 'No solutions yet')}
                    description={t('成为第一个分享思路的人', 'Be the first to share your approach')}
                    primaryAction={{ label: t('发布题解', 'Post Solution'), href: '/solutions?action=create' }}
                  />
                ) : (
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
                )}
              </section>
            </div>
          )}
        </PageContainer>
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
