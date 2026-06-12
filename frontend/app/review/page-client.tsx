'use client'

import { Suspense } from 'react'
import Link from 'next/link'
import {
  ArrowLeft,
  XCircle,
  CheckCircle,
  AlertTriangle,
  Trash2,
  RefreshCw,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageContainer, Panel, PanelHeader, EmptyState } from '@/components/layout'
import { useReviewData } from './hooks/use-review-data'
import { getQuestionTitle, getSourceInfo, getReviewUrl } from './lib/review-utils'

export default function ReviewClient() {
  return (
    <Suspense fallback={<ReviewLoading />}>
      <ReviewPageContent />
    </Suspense>
  )
}

function ReviewLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent" />
    </div>
  )
}

function ReviewPageContent() {
  const {
    wrongQuestions,
    loading,
    error,
    fetchData,
    handleDelete,
    clearError,
    push,
  } = useReviewData()

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center p-8">
          <AlertTriangle className="size-12 text-destructive mx-auto mb-4" strokeWidth={1.5} />
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => { clearError(); fetchData() }}>
            重试
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回">
            <Link href="/dashboard">
              <ArrowLeft className="size-5" strokeWidth={1.5} />
            </Link>
          </Button>
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">错题本</h1>
          <Button
            variant="ghost"
            size="icon"
            onClick={fetchData}
            className="ml-auto"
            aria-label="刷新"
          >
            <RefreshCw className="size-4" strokeWidth={1.5} />
          </Button>
        </div>
      </header>

      <main className="bg-background min-h-[calc(100vh-3.5rem)]">
        <PageContainer className="py-8">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent" />
            </div>
          ) : wrongQuestions.length === 0 ? (
            <EmptyState
              icon={CheckCircle}
              title="没有错题"
              description="所有题目都答对了！继续保持。"
            />
          ) : (
            <Panel>
              <PanelHeader title="错题列表" count={`${wrongQuestions.length} 道`} />
              <div className="divide-y divide-border">
                {wrongQuestions.map((wq) => {
                  const { type: sourceType, label: sourceLabel } = getSourceInfo(wq)
                  const questionTitle = getQuestionTitle(wq)
                  const tags: string[] = []
                  if (sourceLabel) tags.push(sourceLabel)
                  if (wq.exercise_type) tags.push(wq.exercise_type)
                  tags.push(`错误 ${wq.error_count} 次`)

                  return (
                    <article
                      key={wq.id}
                      className="px-6 py-4 flex items-center gap-4 hover:bg-muted/30"
                    >
                      {wq.is_resolved ? (
                        <CheckCircle className="size-4 text-green-500 flex-shrink-0" strokeWidth={1.5} />
                      ) : (
                        <XCircle className="size-4 text-red-500 flex-shrink-0" strokeWidth={1.5} />
                      )}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium truncate">{questionTitle}</h3>
                        <p className="text-xs text-muted-foreground mt-1">{tags.join(' · ')}</p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(wq.id)}
                          aria-label="删除"
                        >
                          <Trash2 className="size-4 text-muted-foreground hover:text-red-500" strokeWidth={1.5} />
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => push(getReviewUrl(wq))}
                        >
                          复习
                          <ChevronRight className="size-4 ml-1" strokeWidth={1.5} />
                        </Button>
                      </div>
                    </article>
                  )
                })}
              </div>
            </Panel>
          )}
        </PageContainer>
      </main>
    </div>
  )
}
