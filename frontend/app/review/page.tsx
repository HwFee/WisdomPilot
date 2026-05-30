'use client'

import { useEffect, useState, Suspense } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Brain, XCircle, CheckCircle, AlertTriangle, Trash2, RefreshCw, ChevronRight } from 'lucide-react'
import {
  getWrongQuestions,
  deleteWrongQuestion,
  type WrongQuestionResponse as WrongQuestion,
} from '@/lib/api/review'


export default function ReviewPage() {
  return (
    <Suspense fallback={<ReviewLoading />}>
      <ReviewPageContent />
    </Suspense>
  )
}

function ReviewLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent"></div>
    </div>
  )
}

function ReviewPageContent() {
  const { push } = useRouter()
  const [wrongQuestions, setWrongQuestions] = useState<WrongQuestion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const token = typeof window !== 'undefined' ? localStorage.getItem('token:v1') : null

  useEffect(() => {
    if (!token) {
      push('/login')
      return
    }
    fetchData()
  }, [push, token])

  const fetchData = async () => {
    if (!token) {
      push('/login')
      return
    }
    try {
      setLoading(true)

      const wrongData = await getWrongQuestions(token).catch(() => ({ wrong_questions: [], total: 0, unresolved_count: 0 }))
      setWrongQuestions(wrongData.wrong_questions || [])
    } catch {
      setError('获取错题数据失败')
    } finally {
      setLoading(false)
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'choice': return '选择题'
      case 'programming': return '编程题'
      case 'fill_blank': return '填空题'
      default: return type
    }
  }

  const handleDeleteWrongQuestion = async (wrongQuestionId: string) => {
    if (!confirm('确定要删除这条错题记录吗？')) return
    if (!token) return

    try {
      await deleteWrongQuestion(wrongQuestionId, token)
      setWrongQuestions(prev => prev.filter(wq => wq.id !== wrongQuestionId))
    } catch {
      alert('删除失败，请稍后重试')
    }
  }

  const handleReview = async (wq: WrongQuestion) => {
    if (!token) return
    const sourceType = wq.source_type || (wq.exercise_key?.startsWith('arena-') ? 'arena' : 'mastery')
    const keyParts = wq.exercise_key?.split('-') || []
    let questionIdFromKey = ''

    if (sourceType === 'mastery' && keyParts.length >= 4) {
      questionIdFromKey = keyParts[3]
    } else if (sourceType === 'arena' && keyParts.length >= 3) {
      questionIdFromKey = keyParts[2]
    }

    if (sourceType === 'arena' && token) {
      // 挑战之路: 直接跳转到挑战之路页面（独立于课程）
      push('/arena')
    } else if (sourceType === 'mastery' && wq.course_id) {
      const chapterParam = wq.chapter_id || ''
      const questionParam = questionIdFromKey || ''
      const sectionParam = wq.section_id || ''
      push(`/mastery/${wq.course_id}?chapter=${chapterParam}&section=${sectionParam}&exercise=${questionParam}&skip=1`)
    } else if (wq.course_id) {
      push(`/mastery/${wq.course_id}`)
    }
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center p-8">
          <AlertTriangle className="size-12 text-red-500 mx-auto mb-4" />
          <p className="text-muted-foreground mb-4">{error}</p>
          <button type="button"
            onClick={() => { setError(null); fetchData() }}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm"
          >
            重试
          </button>
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
            <button type="button"
              onClick={fetchData}
              className="p-2 text-muted-foreground hover:text-foreground rounded-lg transition-colors"
              title="刷新"
            >
              <RefreshCw className="size-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          {/* 错题列表 */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent"></div>
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
                // 提取题目标题
                const textContent = wq.exercise_content?.text
                const textStr = typeof textContent === 'string' ? textContent : ''
                const titleFromContent = wq.exercise_content?.title
                const titleStr = typeof titleFromContent === 'string' ? titleFromContent : ''
                const questionTitle: string = wq.question_title || titleStr ||
                  (textStr ? (textStr.length > 60 ? textStr.substring(0, 60) + '...' : textStr) : getTypeLabel(wq.exercise_type))

                const sourceType = wq.source_type || (wq.exercise_key?.startsWith('arena-') ? 'arena' : 'mastery')
                const sourceLabel = wq.source_label || (sourceType === 'arena' ? '挑战之路' : '精进之路')

                return (
                  <div
                    key={wq.id}
                    className="bg-card rounded-xl border border-border p-4 hover:border-primary/30 transition-all"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        {/* 标题 */}
                        <div className="flex items-center gap-2 mb-2">
                          {wq.is_resolved ? (
                            <CheckCircle className="size-4 text-green-500 flex-shrink-0" />
                          ) : (
                            <XCircle className="size-4 text-red-500 flex-shrink-0" />
                          )}
                          <span className="font-medium text-foreground truncate">{questionTitle}</span>
                        </div>

                        {/* 标签 */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            sourceType === 'arena' ? 'bg-purple-500/10 text-purple-500' : 'bg-blue-500/10 text-blue-500'
                          }`}>
                            {sourceLabel}
                          </span>
                          <span className="text-xs px-2 py-0.5 bg-muted rounded-full">{getTypeLabel(wq.exercise_type)}</span>
                          <span className="text-xs text-muted-foreground">错误 {wq.error_count} 次</span>
                        </div>
                      </div>

                      {/* 操作按钮 */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button type="button"
                          onClick={() => handleDeleteWrongQuestion(wq.id)}
                          className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                          title="删除"
                        >
                          <Trash2 className="size-4" />
                        </button>
                        <button type="button"
                          onClick={() => handleReview(wq)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-all"
                        >
                          复习
                          <ChevronRight className="size-4" />
                        </button>
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
