'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Sparkles, Target, TrendingUp, BookOpen, Code2, ChevronRight, RefreshCw } from 'lucide-react'
import { getExerciseRecommendations, type ExerciseRecommendItem, type KnowledgeState } from '@/lib/api/vector'

interface RecommendedExercisesProps {
  token: string
  limit?: number
  showKnowledgeState?: boolean
  compact?: boolean
}

export function RecommendedExercises({
  token,
  limit = 5,
  showKnowledgeState = true,
  compact = false
}: RecommendedExercisesProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [recommendations, setRecommendations] = useState<ExerciseRecommendItem[]>([])
  const [knowledgeState, setKnowledgeState] = useState<KnowledgeState | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchRecommendations = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getExerciseRecommendations(token, { limit })
      setRecommendations(data.recommendations)
      setKnowledgeState(data.knowledge_state)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (token) {
      fetchRecommendations()
    }
  }, [token, limit])

  const getDifficultyColor = (diff: number) => {
    switch (diff) {
      case 1: return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 2: return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
      case 3: return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 4: return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 5: return 'bg-red-500/20 text-red-400 border-red-500/30'
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-8 bg-slate-700 rounded w-1/3"></div>
        <div className="h-20 bg-slate-700 rounded"></div>
        <div className="h-20 bg-slate-700 rounded"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-4">
        <p className="text-red-400 text-sm">{error}</p>
        <button
          onClick={fetchRecommendations}
          className="mt-2 text-indigo-400 text-sm hover:underline"
        >
          重试
        </button>
      </div>
    )
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {recommendations.slice(0, 3).map((rec, i) => (
          <button
            key={rec.exercise_id}
            onClick={() => router.push(`/exercise/${rec.exercise_id}`)}
            className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-700/50 transition-colors text-left"
          >
            <span className="text-xs font-medium text-indigo-400">#{i + 1}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${getDifficultyColor(rec.difficulty)}`}>
              {rec.difficulty_label}
            </span>
            <span className="flex-1 text-sm text-slate-300 truncate">
              {rec.title || `题目 #${rec.source_id}`}
            </span>
            <ChevronRight className="w-4 h-4 text-slate-500" />
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Knowledge State */}
      {showKnowledgeState && knowledgeState && (
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              <span className="text-sm font-medium text-white">学习状态</span>
            </div>
            <button
              onClick={fetchRecommendations}
              disabled={loading}
              className="p-1.5 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-lg font-bold text-indigo-400">{knowledgeState.estimated_level.toFixed(1)}</p>
              <p className="text-xs text-slate-500">水平估算</p>
            </div>
            <div>
              <p className="text-lg font-bold text-white">{knowledgeState.target_difficulty_label}</p>
              <p className="text-xs text-slate-500">目标难度</p>
            </div>
            <div>
              <p className="text-lg font-bold text-emerald-400">{knowledgeState.accuracy}%</p>
              <p className="text-xs text-slate-500">正确率</p>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-medium text-white">智能推荐</span>
          </div>
          <span className="text-xs text-slate-500">{recommendations.length} 题</span>
        </div>

        <div className="space-y-2">
          {recommendations.map((rec, i) => (
            <button
              key={rec.exercise_id}
              onClick={() => router.push(`/exercise/${rec.exercise_id}`)}
              className="w-full bg-slate-800/30 hover:bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 transition-all text-left group"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded">
                      #{i + 1}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded border ${getDifficultyColor(rec.difficulty)}`}>
                      {rec.difficulty_label}
                    </span>
                    <span className="text-xs text-slate-500">
                      {rec.type === 'programming' ? '编程' : rec.type === 'choice' ? '选择' : '填空'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 truncate mb-1">
                    {rec.title || `题目 #${rec.source_id}`}
                  </p>
                  {rec.reason && (
                    <p className="text-xs text-slate-500 line-clamp-1">{rec.reason}</p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-indigo-400">{(rec.similarity * 100).toFixed(0)}%</p>
                  <p className="text-xs text-slate-500">匹配</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* View More */}
      <button
        onClick={() => router.push('/test-vector')}
        className="w-full text-center py-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
      >
        查看更多推荐 →
      </button>
    </div>
  )
}
