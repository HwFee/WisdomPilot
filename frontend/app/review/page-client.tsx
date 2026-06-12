'use client'

import { Suspense } from 'react'
import Link from 'next/link'
import {
  ArrowLeft,
  Brain,
  XCircle,
  CheckCircle,
  AlertTriangle,
  Trash2,
  RefreshCw,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
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
          <AlertTriangle className="size-12 text-red-500 mx-auto mb-4" />
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button
            type="button"
            onClick={() => { clearError(); fetchData() }}
          >
            重试
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
              <ArrowLeft className="size-4" />
              <span className="text-sm">返回</span>
            </Link>
            <div className="flex items-center gap-2">
              <Brain className="size-5 text-primary" />
              <span className="font-semibold text-foreground">错题本</span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={fetchData}
              title="刷新"
              aria-label="刷新"
            >
              <RefreshCw className="size-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent" />
            </div>
          ) : wrongQuestions.length === 0 ? (
            <div className="text-center py-16 bg-card rounded-2xl border border-border">
              <CheckCircle className="size-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">暂无错题</h3>
              <p className="text-sm text-muted-foreground">继续保持，做错的题目会自动记录</p>
            </div>
          ) : (
            <div className="flex flex-col gap-y-3">
              {wrongQuestions.map((wq) => {
                const { type: sourceType, label: sourceLabel } = getSourceInfo(wq)
                const questionTitle = getQuestionTitle(wq)

                return (
                  <div
                    key={wq.id}
                    className="bg-card rounded-xl border border-border p-4 hover:border-primary/30 transition-all"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        {/* Title */}
                        <div className="flex items-center gap-2 mb-2">
                          {wq.is_resolved ? (
                            <CheckCircle className="size-4 text-green-500 flex-shrink-0" />
                          ) : (
                            <XCircle className="size-4 text-red-500 flex-shrink-0" />
                          )}
                          <span className="font-medium text-foreground truncate">{questionTitle}</span>
                        </div>

                        {/* Tags */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            sourceType === 'arena'
                              ? 'bg-purple-500/10 text-purple-500'
                              : 'bg-blue-500/10 text-blue-500'
                          }`}>
                            {sourceLabel}
                          </span>
                          <span className="text-xs px-2 py-0.5 bg-muted rounded-full">{wq.exercise_type}</span>
                          <span className="text-xs text-muted-foreground">错误 {wq.error_count} 次</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(wq.id)}
                          className="text-muted-foreground hover:text-red-500"
                          title="删除"
                          aria-label="删除"
                        >
                          <Trash2 className="size-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={() => push(getReviewUrl(wq))}
                        >
                          复习
                          <ChevronRight className="size-4 ml-1" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
