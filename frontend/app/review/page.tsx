'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Brain, Clock, Target, TrendingDown, ChevronRight, CheckCircle, XCircle, Flame, BookOpen } from 'lucide-react'

interface ReviewItem {
  exercise_id: number
  exercise_type: string
  exercise_difficulty: number
  knowledge_points: string[]
  priority: number
  repetition: {
    review_count: number
    days_overdue: number
    is_due: boolean
  }
}

interface WeakPoint {
  id: string
  knowledge_point: string
  error_count: number
  mastery_level: number
  weakness_score: number
}

interface ReviewStats {
  total_due: number
  total_scheduled: number
  reviewed_today: number
  streak_days: number
  weak_points_count: number
}

export default function ReviewPage() {
  const router = useRouter()
  const [reviewQueue, setReviewQueue] = useState<ReviewItem[]>([])
  const [weakPoints, setWeakPoints] = useState<WeakPoint[]>([])
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'queue' | 'weak'>('queue')

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

      // 并行获取数据
      const [queueRes, weakRes, statsRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/review/queue`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/review/weak-points`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/review/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ])

      if (queueRes.ok) {
        const data = await queueRes.json()
        setReviewQueue(data.items || [])
      }

      if (weakRes.ok) {
        const data = await weakRes.json()
        setWeakPoints(data.weak_points || [])
      }

      if (statsRes.ok) {
        const data = await statsRes.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Failed to fetch review data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartReview = (exerciseId: number) => {
    router.push(`/exercise/${exerciseId}?mode=review`)
  }

  const handleTargetPractice = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/review/weak-points/target`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ limit: 5 })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.exercises.length > 0) {
          router.push(`/exercise/${data.exercises[0].id}?mode=target`)
        }
      }
    } catch (error) {
      console.error('Failed to start target practice:', error)
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
          ) : (
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
