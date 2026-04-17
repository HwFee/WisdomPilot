'use client'

import { useEffect, useState, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, Brain, Clock, Target, TrendingDown, ChevronRight, CheckCircle, XCircle, Flame, BookOpen, BarChart3, AlertTriangle, Star } from 'lucide-react'
import { FavoriteButton } from '@/components/exercise/FavoriteButton'
import {
  getReviewQueue,
  getWeakPoints,
  getReviewStats,
  getWrongQuestions,
  getWeakPointsAnalysis,
  getReviewReminders,
  type ReviewQueueItem as ReviewItem,
  type WeakPointResponse as WeakPoint,
  type WrongQuestionResponse as WrongQuestion,
  type KnowledgePointAnalysis,
  type ReviewReminderResponse as ReviewReminder,
  type ReviewStatsResponse as ReviewStats,
  type WeakPointAnalysisResponse,
} from '@/lib/api/review'
import { getActiveChallengeSession } from '@/lib/api/learning-path'

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
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
    </div>
  )
}

function ReviewPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [reviewQueue, setReviewQueue] = useState<ReviewItem[]>([])
  const [weakPoints, setWeakPoints] = useState<WeakPoint[]>([])
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'queue' | 'weak' | 'wrong' | 'analysis'>('queue')
  const [wrongQuestions, setWrongQuestions] = useState<WrongQuestion[]>([])
  const [analysisData, setAnalysisData] = useState<{
    knowledge_points: KnowledgePointAnalysis[]
    weakest_knowledge_points: KnowledgePointAnalysis[]
    strongest_knowledge_points: KnowledgePointAnalysis[]
    total_knowledge_points: number
    overall_error_rate: number
  } | null>(null)
  const [reviewReminders, setReviewReminders] = useState<ReviewReminder | null>(null)
  const [practiceMode, setPracticeMode] = useState<'quick' | 'deep' | 'specific'>('quick')

  // Handle URL query parameter for initial tab
  useEffect(() => {
    const type = searchParams.get('type')
    if (type === 'wrong' || type === 'weak' || type === 'analysis') {
      setActiveTab(type)
    }
  }, [searchParams])

  useEffect(() => {
    const token = localStorage.getItem('token')

    if (!token) {
      router.push('/login')
      return
    }

    fetchData()
  }, [router])

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')

      if (!token) {
        router.push('/login')
        return
      }

      // 并行获取数据 - 使用封装好的 API 函数
      const [queueData, weakData, statsData, wrongData, analysisData, remindersData] = await Promise.all([
        getReviewQueue(token).catch(() => ({ items: [], total_due: 0, total_scheduled: 0 })),
        getWeakPoints(token).catch(() => ({ weak_points: [], total: 0 })),
        getReviewStats(token).catch(() => null),
        getWrongQuestions(token).catch(() => ({ wrong_questions: [], total: 0, unresolved_count: 0 })),
        getWeakPointsAnalysis(token).catch(() => null),
        getReviewReminders(token).catch(() => null),
      ])

      setReviewQueue(queueData.items || [])
      setWeakPoints(weakData.weak_points || [])
      setStats(statsData)
      setWrongQuestions(wrongData.wrong_questions || [])
      setAnalysisData(analysisData)
      setReviewReminders(remindersData)
    } catch {
      setError('获取错题本数据失败，请确认后端是否正在运行 (端口 8000)')
    } finally {
      setLoading(false)
    }
  }

  // 错误状态显示
  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center p-8 max-w-md">
          <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">网络错误</h3>
          <p className="text-sm text-muted-foreground mb-4 whitespace-pre-wrap">{error}</p>
          <button
            onClick={() => {
              setError(null)
              setLoading(true)
              fetchData()
            }}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  const handleStartReview = (exerciseId: number) => {
    router.push(`/exercise/${exerciseId}?mode=review`)
  }

  const handleTargetPractice = async () => {
    try {
      const token = localStorage.getItem('token')
      const limit = practiceMode === 'quick' ? 5 : practiceMode === 'deep' ? 10 : 5
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/review/practice/enhanced`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ mode: practiceMode, limit })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.exercises && data.exercises.length > 0) {
          router.push(`/exercise/${data.exercises[0].id}?mode=target`)
        }
      }
    } catch {
      // 静默处理错误
    }
  }

  const getMasteryColor = (level: number) => {
    if (level <= 1) return 'text-red-500'
    if (level <= 2) return 'text-orange-500'
    if (level <= 3) return 'text-yellow-500'
    if (level <= 4) return 'text-green-500'
    return 'text-primary'
  }

  const getMasteryBg = (level: number) => {
    if (level <= 1) return 'bg-red-500'
    if (level <= 2) return 'bg-orange-500'
    if (level <= 3) return 'bg-yellow-500'
    if (level <= 4) return 'bg-green-500'
    return 'bg-primary'
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'choice': return '选择题'
      case 'programming': return '编程题'
      case 'fill_blank': return '填空题'
      default: return type
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors group">
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
              <span className="text-sm">返回</span>
            </Link>
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              <span className="font-semibold text-foreground">科学复习</span>
            </div>
          </div>
        </div>
      </header>

      <main className="pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Stats Cards */}
          {stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              <div className="bg-card rounded-xl border border-border p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
                    <Clock className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{stats.total_due}</p>
                    <p className="text-xs text-muted-foreground">待复习</p>
                  </div>
                </div>
              </div>

              <div className="bg-card rounded-xl border border-border p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-500/10 rounded-xl flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{stats.reviewed_today}</p>
                    <p className="text-xs text-muted-foreground">今日已复习</p>
                  </div>
                </div>
              </div>

              <div className="bg-card rounded-xl border border-border p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-orange-500/10 rounded-xl flex items-center justify-center">
                    <TrendingDown className="w-5 h-5 text-orange-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{stats.weak_points_count}</p>
                    <p className="text-xs text-muted-foreground">薄弱点</p>
                  </div>
                </div>
              </div>

              <div className="bg-card rounded-xl border border-border p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-yellow-500/10 rounded-xl flex items-center justify-center">
                    <Flame className="w-5 h-5 text-yellow-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{stats.streak_days}</p>
                    <p className="text-xs text-muted-foreground">连续天数</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="mb-6">
            <div className="inline-flex items-center bg-muted rounded-xl p-1">
              <button
                onClick={() => setActiveTab('queue')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'queue'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Clock className="w-4 h-4" />
                <span>复习队列</span>
                {reviewQueue.length > 0 && (
                  <span className="px-1.5 py-0.5 text-xs bg-primary text-primary-foreground rounded-full">{reviewQueue.length}</span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('weak')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'weak'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <TrendingDown className="w-4 h-4" />
                <span>薄弱点</span>
                {weakPoints.length > 0 && (
                  <span className="px-1.5 py-0.5 text-xs bg-orange-500 text-white rounded-full">{weakPoints.length}</span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('wrong')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'wrong'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <AlertTriangle className="w-4 h-4" />
                <span>错题本</span>
                {wrongQuestions.filter(w => !w.is_resolved).length > 0 && (
                  <span className="px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                    {wrongQuestions.filter(w => !w.is_resolved).length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('analysis')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'analysis'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>分析</span>
              </button>
            </div>
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
            </div>
          ) : activeTab === 'queue' ? (
            <>
              {/* Review Queue */}
              {reviewQueue.length === 0 ? (
                <div className="text-center py-16 bg-card rounded-2xl border border-border">
                  <div className="w-16 h-16 bg-green-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-green-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">暂无待复习内容</h3>
                  <p className="text-sm text-muted-foreground">继续保持学习，新的复习内容会自动加入队列</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {reviewQueue.map((item, index) => (
                    <div
                      key={item.exercise_id}
                      className="bg-card rounded-xl border border-border p-4 flex items-center justify-between hover:border-primary/40 hover:shadow-md transition-all cursor-pointer group"
                      onClick={() => handleStartReview(item.exercise_id)}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                          item.repetition.days_overdue > 0 ? 'bg-red-500/10' : 'bg-primary/10'
                        }`}>
                          <span className={`text-sm font-bold ${
                            item.repetition.days_overdue > 0 ? 'text-red-500' : 'text-primary'
                          }`}>
                            {index + 1}
                          </span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-foreground">{getTypeLabel(item.exercise_type)}</span>
                            <span className="text-xs px-2 py-0.5 bg-muted rounded-full">难度 {item.exercise_difficulty}</span>
                          </div>
                          <div className="flex items-center gap-3 text-sm text-muted-foreground">
                            {item.repetition.days_overdue > 0 ? (
                              <span className="flex items-center gap-1 text-red-500">
                                <Clock className="w-3 h-3" />
                                逾期 {item.repetition.days_overdue} 天
                              </span>
                            ) : (
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                今日到期
                              </span>
                            )}
                            <span>复习 {item.repetition.review_count} 次</span>
                          </div>
                          <div className="flex gap-1 mt-2">
                            {item.knowledge_points.slice(0, 3).map((kp, i) => (
                              <span key={i} className="text-xs px-2 py-0.5 bg-primary/5 text-primary rounded-full">
                                {kp}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : activeTab === 'weak' ? (
            <>
              {/* Weak Points */}
              <div className="mb-6">
                <button
                  onClick={handleTargetPractice}
                  className="w-full bg-gradient-to-r from-primary to-primary-600 text-primary-foreground rounded-xl p-4 flex items-center justify-center gap-2 font-medium hover:shadow-lg hover:shadow-primary/25 transition-all"
                >
                  <Target className="w-5 h-5" />
                  开始针对性练习
                </button>
              </div>

              {weakPoints.length === 0 ? (
                <div className="text-center py-16 bg-card rounded-2xl border border-border">
                  <div className="w-16 h-16 bg-green-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-green-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">暂无薄弱点</h3>
                  <p className="text-sm text-muted-foreground">继续学习，系统会自动识别你的薄弱知识点</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {weakPoints.map((wp) => (
                    <div
                      key={wp.id}
                      className="bg-card rounded-xl border border-border p-4 hover:border-primary/30 transition-all"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <BookOpen className="w-4 h-4 text-primary" />
                            <h4 className="font-medium text-foreground">{wp.knowledge_point}</h4>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <XCircle className="w-3 h-3 text-red-500" />
                              错误 {wp.error_count} 次
                            </span>
                            <span>掌握度 {wp.mastery_level}/5</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-full ${
                            wp.mastery_level <= 2 ? 'bg-red-500/10' : wp.mastery_level <= 3 ? 'bg-yellow-500/10' : 'bg-green-500/10'
                          }`}>
                            <span className={`font-bold ${getMasteryColor(wp.mastery_level)}`}>
                              Lv.{wp.mastery_level}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">掌握程度</p>
                        </div>
                      </div>
                      {/* Progress bar */}
                      <div className="mt-4 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all ${getMasteryBg(wp.mastery_level)}`}
                          style={{ width: `${(wp.mastery_level / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : activeTab === 'wrong' ? (
            <>
              {/* Wrong Questions Notebook */}
              {wrongQuestions.length === 0 ? (
                <div className="text-center py-16 bg-card rounded-2xl border border-border">
                  <div className="w-16 h-16 bg-green-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-green-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">暂无错题记录</h3>
                  <p className="text-sm text-muted-foreground">继续保持，做错的题目会自动记录到这里</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {wrongQuestions.map((wq) => {
                    // 解析来源信息
                    const sourceType = wq.source_type || (wq.exercise_key?.startsWith('arena-') ? 'arena' :
                      wq.exercise_key?.startsWith('mastery-') ? 'mastery' :
                      wq.exercise_key?.startsWith('enhanced-') ? 'enhanced' : 'unknown')
                    const sourceLabel = wq.source_label || (sourceType === 'arena' ? '挑战之路' :
                      sourceType === 'mastery' ? '精进之路' :
                      sourceType === 'enhanced' ? '强化测试' : '未知来源')

                    // 提取题目标题
                    const textContent = wq.exercise_content?.text
                    const textStr = typeof textContent === 'string' ? textContent : ''
                    const titleFromContent = wq.exercise_content?.title
                    const titleStr = typeof titleFromContent === 'string' ? titleFromContent : ''
                    const questionTitle: string = wq.question_title || titleStr ||
                      (textStr ?
                        (textStr.length > 50 ?
                          textStr.substring(0, 50) + '...' :
                          textStr) :
                        getTypeLabel(wq.exercise_type))

                    // 从 exercise_key 提取 question_id 用于跳转
                    // 格式: mastery-{courseId}-{chapterId}-{questionId} 或 arena-{courseId}-{questionId}
                    const keyParts = wq.exercise_key?.split('-') || []
                    let questionIdFromKey = ''
                    let chapterIdFromKey = wq.chapter_id || ''

                    if (sourceType === 'mastery' && keyParts.length >= 4) {
                      // mastery-{courseId}-{chapterId}-{questionId}
                      chapterIdFromKey = keyParts[2]
                      questionIdFromKey = keyParts[3]
                    } else if (sourceType === 'arena' && keyParts.length >= 3) {
                      // arena-{courseId}-{questionId}
                      questionIdFromKey = keyParts[2]
                    } else if (sourceType === 'enhanced' && keyParts.length >= 4) {
                      // enhanced-{courseId}-{sessionId}-{questionId}
                      questionIdFromKey = keyParts[3]
                    }

                    return (
                      <div
                        key={wq.id}
                        className="bg-card rounded-xl border border-border p-4 hover:border-primary/30 transition-all"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            {/* 标题行 */}
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              <AlertTriangle className={`w-4 h-4 flex-shrink-0 ${wq.is_resolved ? 'text-green-500' : 'text-red-500'}`} />
                              <span className="font-medium text-foreground truncate">{questionTitle}</span>
                            </div>

                            {/* 来源和状态标签 */}
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              <span className={`text-xs px-2 py-0.5 rounded-full ${
                                sourceType === 'arena' ? 'bg-purple-500/10 text-purple-500' :
                                sourceType === 'mastery' ? 'bg-blue-500/10 text-blue-500' :
                                'bg-muted text-muted-foreground'
                              }`}>
                                {sourceLabel}
                              </span>
                              <span className="text-xs px-2 py-0.5 bg-muted rounded-full">{getTypeLabel(wq.exercise_type)}</span>
                              <span className="text-xs px-2 py-0.5 bg-muted rounded-full">难度 {wq.exercise_difficulty}</span>
                              {wq.is_resolved && (
                                <span className="text-xs px-2 py-0.5 bg-green-500/10 text-green-500 rounded-full">已掌握</span>
                              )}
                            </div>

                            {/* 错误次数和时间 */}
                            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                              <span className="flex items-center gap-1">
                                <XCircle className="w-3 h-3 text-red-500" />
                                错误 {wq.error_count} 次
                              </span>
                              <span>最近 {new Date(wq.last_error_at).toLocaleDateString()}</span>
                            </div>

                            {/* 知识点 */}
                            <div className="flex gap-1 flex-wrap">
                              {wq.knowledge_points.slice(0, 3).map((kp, i) => (
                                <span key={i} className="text-xs px-2 py-0.5 bg-primary/5 text-primary rounded-full">
                                  {kp}
                                </span>
                              ))}
                            </div>
                          </div>
                          
                          <div className="flex flex-col items-end gap-2">
                            {/* 收藏按钮 - 直接传错题本的数据 */}
                            <FavoriteButton
                              exerciseKey={wq.exercise_key || undefined}
                              courseId={wq.course_id}
                              exerciseId={wq.exercise_id ?? undefined}
                              chapterId={wq.chapter_id ?? undefined}
                              exerciseContent={wq.exercise_content as { title?: string; text?: string; description?: string; options?: string[] } | undefined}
                              exerciseType={wq.exercise_type}
                              exerciseDifficulty={wq.exercise_difficulty}
                              knowledgePoints={wq.knowledge_points}
                              size="sm"
                              onFavoriteChange={() => {
                                // 收藏状态已更新
                              }}
                            />

                            {/* 复习按钮 */}
                            <button
                            onClick={async () => {
                              const token = localStorage.getItem('token')
                              // 根据来源类型跳转到不同页面
                              if (sourceType === 'arena' && wq.course_id && token) {
                                // 挑战之路: 跳转到挑战之路页面（路由参数是 courseId）
                                // exerciseIndex 用于定位到具体题目
                                try {
                                  const result = await getActiveChallengeSession(wq.course_id, token)
                                  if (result.session) {
                                    // 找到该题目在练习列表中的索引
                                    const questionIdNum = parseInt(questionIdFromKey)
                                    const exerciseInfo = result.exercise_map[questionIdNum]
                                    const targetIndex = exerciseInfo?.exercise_index ?? result.session.current_index
                                    // 路由是 /arena/[courseId]，不是 session.id
                                    router.push(`/arena/${wq.course_id}?exerciseIndex=${targetIndex}`)
                                  } else {
                                    // 没有活跃会话，跳转到仪表盘让用户开始新挑战
                                    router.push('/dashboard?tab=challenge')
                                  }
                                } catch {
                                  router.push('/dashboard?tab=challenge')
                                }
                              } else if (sourceType === 'mastery' && wq.course_id) {
                                // 精进之路: 跳转到具体章节和题目（跳过知识点直接进入测试）
                                // exercise 参数是 question_id，精进之路页面会找到对应的索引
                                const chapterParam = chapterIdFromKey || wq.chapter_id || ''
                                const questionParam = questionIdFromKey || ''
                                router.push(`/mastery/${wq.course_id}?chapter=${chapterParam}&exercise=${questionParam}&skip=1`)
                              } else if (wq.course_id) {
                                // 其他情况: 跳转到精进之路
                                router.push(`/mastery/${wq.course_id}`)
                              }
                            }}
                            className="px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-all flex-shrink-0"
                          >
                            复习
                          </button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          ) : (
            <>
              {/* Analysis Tab */}
              {analysisData && (
                <div className="space-y-6">
                  {/* Overall Stats */}
                  <div className="bg-card rounded-xl border border-border p-4">
                    <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-primary" />
                      整体概况
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-muted/50 rounded-lg p-3">
                        <p className="text-2xl font-bold text-foreground">{analysisData.total_knowledge_points}</p>
                        <p className="text-xs text-muted-foreground">知识点总数</p>
                      </div>
                      <div className="bg-muted/50 rounded-lg p-3">
                        <p className="text-2xl font-bold text-red-500">{(analysisData.overall_error_rate * 100).toFixed(1)}%</p>
                        <p className="text-xs text-muted-foreground">整体错误率</p>
                      </div>
                    </div>
                  </div>

                  {/* Ebbinghaus Schedule */}
                  {reviewReminders && reviewReminders.ebbinghaus_schedule.length > 0 && (
                    <div className="bg-card rounded-xl border border-border p-4">
                      <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                        <Clock className="w-5 h-5 text-primary" />
                        艾宾浩斯复习计划
                      </h3>
                      <div className="space-y-2">
                        {reviewReminders.ebbinghaus_schedule.map((slot) => (
                          <div key={slot.day} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                            <div className="flex items-center gap-3">
                              <span className="text-sm font-medium text-foreground">{slot.label}</span>
                              <span className="text-xs text-muted-foreground">第 {slot.day} 天</span>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                              slot.count > 0 ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
                            }`}>
                              {slot.count} 题
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Weakest Knowledge Points */}
                  {analysisData.weakest_knowledge_points && analysisData.weakest_knowledge_points.length > 0 && (
                    <div className="bg-card rounded-xl border border-border p-4">
                      <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                        <TrendingDown className="w-5 h-5 text-red-500" />
                        最薄弱知识点
                      </h3>
                      <div className="space-y-3">
                        {analysisData.weakest_knowledge_points.slice(0, 5).map((kp, index) => (
                          <div key={kp.knowledge_point} className="space-y-2">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="w-6 h-6 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center text-xs font-bold">
                                  {index + 1}
                                </span>
                                <span className="text-sm font-medium text-foreground">{kp.knowledge_point}</span>
                              </div>
                              <span className="text-sm text-red-500 font-medium">
                                {kp.error_count} 次错误
                              </span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className="h-full bg-red-500 transition-all"
                                style={{ width: `${kp.error_rate * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Practice Mode Selection */}
                  <div className="bg-card rounded-xl border border-border p-4">
                    <h3 className="font-semibold text-foreground mb-4">练习模式</h3>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        onClick={() => setPracticeMode('quick')}
                        className={`p-3 rounded-lg border text-center transition-all ${
                          practiceMode === 'quick'
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-border hover:border-primary/30'
                        }`}
                      >
                        <p className="font-medium text-sm">快速练习</p>
                        <p className="text-xs text-muted-foreground mt-1">5题</p>
                      </button>
                      <button
                        onClick={() => setPracticeMode('deep')}
                        className={`p-3 rounded-lg border text-center transition-all ${
                          practiceMode === 'deep'
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-border hover:border-primary/30'
                        }`}
                      >
                        <p className="font-medium text-sm">深度练习</p>
                        <p className="text-xs text-muted-foreground mt-1">10题</p>
                      </button>
                      <button
                        onClick={() => setPracticeMode('specific')}
                        className={`p-3 rounded-lg border text-center transition-all ${
                          practiceMode === 'specific'
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-border hover:border-primary/30'
                        }`}
                      >
                        <p className="font-medium text-sm">专项突破</p>
                        <p className="text-xs text-muted-foreground mt-1">薄弱点</p>
                      </button>
                    </div>
                    <button
                      onClick={handleTargetPractice}
                      className="w-full mt-4 bg-gradient-to-r from-primary to-primary-600 text-primary-foreground rounded-xl p-4 flex items-center justify-center gap-2 font-medium hover:shadow-lg hover:shadow-primary/25 transition-all"
                    >
                      <Target className="w-5 h-5" />
                      开始{practiceMode === 'quick' ? '快速' : practiceMode === 'deep' ? '深度' : '专项'}练习
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Footer Info */}
      <div className="text-center pb-8">
        <p className="text-sm text-muted-foreground">
          基于艾宾浩斯遗忘曲线 · 间隔复习 · 薄弱点定向练习
        </p>
      </div>
    </div>
  )
}
