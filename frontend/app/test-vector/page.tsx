'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout } from '@/lib/api'
import {
  ArrowLeft, Brain, Target, Loader2, CheckCircle, XCircle,
  Sparkles, TrendingUp, BookOpen, Code2, Star, Info,
  Lightbulb, Zap, BarChart3
} from 'lucide-react'

interface KnowledgeState {
  estimated_level: number
  target_difficulty: number
  target_difficulty_label: string
  total_attempts: number
  accuracy: number
}

interface RecommendedExercise {
  exercise_id: number
  source_id: string
  similarity: number
  difficulty: number
  difficulty_label: string
  type: string
  knowledge_points: string[]
  title: string
  reason: string
  matched_weak_points: string[]
}

interface RecommendResponse {
  user_vector_generated: boolean
  weak_points: string[]
  user_weak_point_count: number
  recommendations: RecommendedExercise[]
  total_candidates: number
  knowledge_state: KnowledgeState | null
}

export default function VectorMatchTestPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [data, setData] = useState<RecommendResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const hasFetched = useRef(false)

  const fetchData = useCallback(async (token: string) => {
    try {
      setIsGenerating(true)
      setError(null)

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/exercises/recommend`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          limit: 10,
          min_difficulty: 1,
          max_difficulty: 5,
          exclude_completed: true
        })
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
      }

      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
      setIsGenerating(false)
    }
  }, [])

  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    if (!token) {
      logout()
      router.push('/login')
      return
    }
    hasFetched.current = true
    fetchData(token)
  }, [router, fetchData])

  const getDifficultyColor = (diff: number) => {
    switch (diff) {
      case 1: return 'text-green-500 bg-green-500/10 border-green-500/30'
      case 2: return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30'
      case 3: return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30'
      case 4: return 'text-orange-500 bg-orange-500/10 border-orange-500/30'
      case 5: return 'text-red-500 bg-red-500/10 border-red-500/30'
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/30'
    }
  }

  const getSimilarityColor = (sim: number) => {
    if (sim >= 0.7) return 'text-green-500'
    if (sim >= 0.5) return 'text-emerald-500'
    if (sim >= 0.3) return 'text-yellow-500'
    return 'text-orange-500'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">分析学习数据中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            <h1 className="text-lg font-semibold">智能题目推荐</h1>
          </div>
          <button
            onClick={() => {
              const token = getStoredToken()
              if (token) fetchData(token)
            }}
            disabled={isGenerating}
            className="ml-auto px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                分析中
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                重新推荐
              </>
            )}
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 pt-20 pb-8">
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 text-red-500">
              <XCircle className="w-5 h-5" />
              <p>{error}</p>
            </div>
          </div>
        )}

        {data && (
          <>
            {/* Knowledge State Card */}
            {data.knowledge_state && (
              <div className="bg-card rounded-xl border border-border p-5 mb-6">
                <h2 className="font-semibold flex items-center gap-2 mb-4">
                  <BarChart3 className="w-5 h-5 text-primary" />
                  学习状态分析
                </h2>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-muted/50 rounded-lg p-4">
                    <p className="text-xs text-muted-foreground mb-1">估算水平</p>
                    <p className="text-2xl font-bold text-primary">
                      {data.knowledge_state.estimated_level.toFixed(1)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">/ 5.0</p>
                  </div>

                  <div className="bg-muted/50 rounded-lg p-4">
                    <p className="text-xs text-muted-foreground mb-1">目标难度</p>
                    <p className="text-2xl font-bold text-primary">
                      {data.knowledge_state.target_difficulty_label}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Level {data.knowledge_state.target_difficulty}
                    </p>
                  </div>

                  <div className="bg-muted/50 rounded-lg p-4">
                    <p className="text-xs text-muted-foreground mb-1">练习次数</p>
                    <p className="text-2xl font-bold">{data.knowledge_state.total_attempts}</p>
                    <p className="text-xs text-muted-foreground mt-1">次</p>
                  </div>

                  <div className="bg-muted/50 rounded-lg p-4">
                    <p className="text-xs text-muted-foreground mb-1">正确率</p>
                    <p className="text-2xl font-bold text-primary">
                      {data.knowledge_state.accuracy}%
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">平均</p>
                  </div>
                </div>
              </div>
            )}

            {/* User Profile Section */}
            <div className="bg-card rounded-xl border border-border p-5 mb-6">
              <h2 className="font-semibold flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-primary" />
                学习画像
              </h2>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-muted/50 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground mb-1">数据状态</p>
                  <div className="flex items-center gap-1">
                    {data.user_vector_generated ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="text-sm font-medium">已建模</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4 text-yellow-500" />
                        <span className="text-sm font-medium">新用户</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="bg-muted/50 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground mb-1">薄弱点</p>
                  <p className="text-xl font-bold">{data.user_weak_point_count}</p>
                </div>

                <div className="bg-muted/50 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground mb-1">候选题目</p>
                  <p className="text-xl font-bold">{data.total_candidates}</p>
                </div>
              </div>

              {/* Weak Points */}
              {data.weak_points.length > 0 && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">薄弱知识点:</p>
                  <div className="flex flex-wrap gap-2">
                    {data.weak_points.map((wp, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-orange-500/10 text-orange-500 rounded-full text-xs font-medium border border-orange-500/30"
                      >
                        {wp}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Recommendations */}
            <div className="bg-card rounded-xl border border-border overflow-hidden">
              <div className="p-4 border-b border-border flex items-center justify-between">
                <h2 className="font-semibold flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary" />
                  推荐题目
                </h2>
                <span className="text-sm text-muted-foreground">
                  共 {data.recommendations.length} 题
                </span>
              </div>

              {data.recommendations.length === 0 ? (
                <div className="p-8 text-center">
                  <BookOpen className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                  <p className="text-muted-foreground">暂无推荐题目</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    完成更多练习后可获得更精准的推荐
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {data.recommendations.map((rec, index) => (
                    <div
                      key={rec.exercise_id}
                      className="p-4 hover:bg-muted/30 transition-colors cursor-pointer"
                      onClick={() => router.push(`/exercise/${rec.exercise_id}`)}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">
                              #{index + 1}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getDifficultyColor(rec.difficulty)}`}>
                              {rec.difficulty_label || `难度${rec.difficulty}`}
                            </span>
                            <span className="flex items-center gap-1 text-muted-foreground text-xs">
                              <Code2 className="w-3 h-3" />
                              {rec.type === 'programming' ? '编程题' : rec.type === 'choice' ? '选择题' : '填空题'}
                            </span>
                          </div>

                          <h3 className="font-medium text-foreground mb-2 line-clamp-1">
                            {rec.title || `题目 #${rec.source_id}`}
                          </h3>

                          {/* Recommendation Reason */}
                          {rec.reason && (
                            <div className="flex items-start gap-2 mb-2 p-2 bg-primary/5 rounded-lg">
                              <Lightbulb className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                              <p className="text-sm text-muted-foreground">{rec.reason}</p>
                            </div>
                          )}

                          {/* Matched Weak Points */}
                          {rec.matched_weak_points && rec.matched_weak_points.length > 0 && (
                            <div className="flex items-center gap-2 mb-2">
                              <Zap className="w-3 h-3 text-orange-500" />
                              <span className="text-xs text-orange-500">针对薄弱点：</span>
                              {rec.matched_weak_points.slice(0, 2).map((wp, i) => (
                                <span key={i} className="px-1.5 py-0.5 bg-orange-500/10 text-orange-500 rounded text-xs">
                                  {wp}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Knowledge Points */}
                          {rec.knowledge_points.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {rec.knowledge_points.slice(0, 3).map((kp, i) => (
                                <span
                                  key={i}
                                  className="px-1.5 py-0.5 bg-muted text-muted-foreground rounded text-xs"
                                >
                                  {kp}
                                </span>
                              ))}
                              {rec.knowledge_points.length > 3 && (
                                <span className="text-xs text-muted-foreground">
                                  +{rec.knowledge_points.length - 3}
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Similarity Score */}
                        <div className="text-right flex-shrink-0">
                          <div className={`text-lg font-bold ${getSimilarityColor(rec.similarity)}`}>
                            {(rec.similarity * 100).toFixed(0)}%
                          </div>
                          <p className="text-xs text-muted-foreground">匹配度</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Algorithm Explanation */}
            <div className="mt-6 bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
              <h3 className="font-medium text-blue-500 mb-2 flex items-center gap-2">
                <Info className="w-4 h-4" />
                自适应推荐算法说明
              </h3>
              <ul className="text-sm text-muted-foreground space-y-1.5">
                <li>• <strong>知识追踪</strong>：根据你的做题历史估算知识水平</li>
                <li>• <strong>最近发展区(ZPD)</strong>：推荐略高于当前水平的题目，实现最佳学习效果</li>
                <li>• <strong>薄弱点定向</strong>：针对你的薄弱知识点推荐练习</li>
                <li>• <strong>多样性保证</strong>：避免重复推荐相似题目，覆盖不同知识点</li>
                <li>• <strong>间隔重复</strong>：避免短期内重复练习同一题目</li>
              </ul>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
