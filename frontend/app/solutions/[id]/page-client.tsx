'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { ArrowLeft, Edit3, Trash2, Heart, Eye, Pin, Megaphone, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageContainer, Panel, PanelHeader } from '@/components/layout'
import { SolutionMarkdown } from '@/components/solutions/SolutionMarkdown'
import { SolutionEditor } from '@/components/solutions/SolutionEditor'
import { useSolutionDetail } from '../hooks/use-solution-detail'

export default function SolutionDetailClient() {
  const params = useParams()
  const solutionId = parseInt(params.id as string)

  const {
    solution,
    loading,
    editMode,
    setEditMode,
    currentUser,
    isAdmin,
    lang,
    handleDelete,
    handleEditSave,
    push,
  } = useSolutionDetail(solutionId)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">{t('加载中...', 'Loading...')}</div>
      </div>
    )
  }

  if (!solution) return null

  const isOwner = currentUser?.id === solution.user_id

  // Edit mode
  if (editMode) {
    return (
      <div className="min-h-screen bg-background">
        <header className="h-14 border-b bg-card">
          <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
            <Button variant="ghost" onClick={() => setEditMode(false)}>
              <ArrowLeft className="size-5 mr-2" strokeWidth={1.5} />
              {t('取消编辑', 'Cancel Edit')}
            </Button>
            <h1 className="text-sm font-semibold uppercase tracking-[2px] ml-4">
              {t('编辑题解', 'Edit Solution')}
            </h1>
          </div>
        </header>
        <main className="bg-background min-h-[calc(100vh-3.5rem)]">
          <PageContainer className="py-8">
            <SolutionEditor
              initialTitle={solution.title}
              initialContent={solution.content}
              initialIsAnnouncement={solution.is_announcement}
              onSave={handleEditSave}
              onCancel={() => setEditMode(false)}
              isAdmin={isAdmin}
              lang={lang}
              isFullPage
            />
          </PageContainer>
        </main>
      </div>
    )
  }

  // View mode
  return (
    <div className="min-h-screen bg-background">
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回首页">
            <Link href="/dashboard">
              <Home className="size-5" strokeWidth={1.5} />
            </Link>
          </Button>
          <Button asChild variant="ghost">
            <Link href="/solutions">
              <ArrowLeft className="size-5 mr-2" strokeWidth={1.5} />
              {t('返回列表', 'Back')}
            </Link>
          </Button>

          {isOwner && (
            <div className="ml-auto flex items-center gap-2">
              <Button variant="secondary" size="sm" onClick={() => setEditMode(true)}>
                <Edit3 className="size-4 mr-1.5" strokeWidth={1.5} />
                {t('编辑', 'Edit')}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDelete(t('确定删除这篇题解吗？', 'Delete this solution?'))}
                className="text-red-500 hover:text-red-600"
              >
                <Trash2 className="size-4 mr-1.5" strokeWidth={1.5} />
                {t('删除', 'Delete')}
              </Button>
            </div>
          )}
        </div>
      </header>

      <main className="bg-background min-h-[calc(100vh-3.5rem)]">
        <PageContainer className="py-8">
          <Panel>
            <PanelHeader
              title={solution.title}
              action={
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  {solution.is_pinned && <Pin className="size-4 text-foreground" strokeWidth={1.5} />}
                  {solution.is_announcement && <Megaphone className="size-4 text-foreground" strokeWidth={1.5} />}
                  <span className="flex items-center gap-1">
                    <Eye className="size-3.5" strokeWidth={1.5} />
                    {solution.view_count}
                  </span>
                  <span className="flex items-center gap-1">
                    <Heart className="size-3.5" strokeWidth={1.5} />
                    {solution.like_count}
                  </span>
                </div>
              }
            />

            <div className="px-8 py-6 border-b border-border text-sm text-muted-foreground flex items-center gap-4">
              <span>{solution.username}</span>
              <span suppressHydrationWarning>{new Date(solution.created_at).toLocaleDateString()}</span>
            </div>

            <article className="px-8 py-8">
              <div className="markdown-body">
                <SolutionMarkdown content={solution.content} />
              </div>

              {solution.tags && solution.tags.length > 0 && (
                <footer className="mt-8 pt-6 border-t border-border">
                  <div className="flex flex-wrap gap-2">
                    {solution.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-muted text-sm"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </footer>
              )}
            </article>
          </Panel>
        </PageContainer>
      </main>
    </div>
  )
}
