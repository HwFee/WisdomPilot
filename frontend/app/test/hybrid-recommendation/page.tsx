'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Settings, Play, RefreshCw, Database, Brain, Target,
  CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp,
  Zap, BarChart3, PieChart
} from 'lucide-react'
import { getStoredToken } from '@/lib/api'

interface UserStats {
  accuracy: number
  avg_attempts?: number
  avg_time_spent?: number  // fallback
  total_submissions: number
  current_streak: number
  best_streak: number
  behavior_embedding: number[] | null
  user_level: number
  total_exercises: number
  completed_exercises: number
  // 段位信息
  tier: string
  sub_tier: number
  stars: number
}

interface Recommendation {
  exercise_id: number
  difficulty: number
  knowledge_points: string[]
  final_score: number
  score_breakdown: {
    behavior: number
    embedding: number
    difficulty: number
  }
  reasons: string[]
  title: string
}

interface SystemStatus {
  total_exercises: number
  exercises_with_embedding: number
  embedding_coverage: string
  embedding_service_configured: boolean
  embedding_provider: string
  embedding_model: string
}

interface DebugResponse {
  course_id: number
  user_stats: UserStats
  recommendations: Recommendation[]
  system_status: SystemStatus
  fusion_weights: {
    behavior: number
    embedding: number
    difficulty: number
  }
}

export default function HybridRecommendationTestPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [debugData, setDebugData] = useState<DebugResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedCourse, setSelectedCourse] = useState(1)
  const [minDifficulty, setMinDifficulty] = useState(1)
  const [maxDifficulty, setMaxDifficulty] = useState(8)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    userStats: true,
    recommendations: true,
    systemStatus: true,
  })

  // API Configuration
  const [apiConfig, setApiConfig] = useState({
    provider: 'openai',
    model: 'text-embedding-3-small',
    apiKey: '',
    baseUrl: '',
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  // 段位显示辅助函数
  const getTierDisplay = (tier: string, subTier: number) => {
    const tierNames: Record<string, string> = {
      bronze: '青铜',
      silver: '白银',
      gold: '黄金',
      platinum: '铂金',
      diamond: '钻石',
      master: '大师',
      grandmaster: '宗师',
      king: '王者',
    }
    const romanNumerals = ['', 'I', 'II', 'III', 'IV', 'V']
    return `${tierNames[tier] || tier} ${romanNumerals[subTier] || subTier}`
  }

  const fetchDebugData = async () => {
    setLoading(true)
    setError(null)
    const token = getStoredToken()
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/courses/recommendation-debug/${selectedCourse}?min_difficulty=${minDifficulty}&max_difficulty=${maxDifficulty}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (!response.ok) throw new Error('Failed to fetch debug data')
      const data = await response.json()
      setDebugData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const recalculateProfile = async () => {
    setLoading(true)
    setError(null)
    const token = getStoredToken()
    if (!token) return

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/courses/${selectedCourse}/recalculate-profile`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (!response.ok) throw new Error('Failed to recalculate profile')
      await fetchDebugData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const batchUpdateEmbeddings = async () => {
    setLoading(true)
    setError(null)
    const token = getStoredToken()
    if (!token) return

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/courses/batch-update-embeddings?limit=20`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (!response.ok) throw new Error('Failed to update embeddings')
      const result = await response.json()
      alert(`Updated ${result.result.updated} exercises, failed ${result.result.failed}`)
      await fetchDebugData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDebugData()
  }, [selectedCourse, minDifficulty, maxDifficulty])

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600 dark:text-green-400'
    if (score >= 0.5) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <Brain className="w-7 h-7 text-primary" />
              混合推荐系统测试
            </h1>
            <p className="text-muted-foreground mt-1">
              测试行为特征、Embedding相似度、难度匹配三维度融合推荐算法
            </p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(parseInt(e.target.value))}
              className="px-3 py-2 rounded-lg border bg-background text-foreground"
            >
              <option value={1}>C语言程序设计</option>
              <option value={2}>C++程序设计</option>
              <option value={3}>Python程序设计</option>
              <option value={4}>Java程序设计</option>
              <option value={5}>Rust程序设计</option>
              <option value={6}>数据结构与算法</option>
              <option value={7}>算法设计与分析</option>
              <option value={8}>离散数学</option>
            </select>
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">难度:</label>
              <select
                value={minDifficulty}
                onChange={(e) => setMinDifficulty(parseInt(e.target.value))}
                className="px-2 py-1.5 rounded border bg-background text-foreground text-sm"
              >
                {[1,2,3,4,5,6,7,8].map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
              <span className="text-muted-foreground">-</span>
              <select
                value={maxDifficulty}
                onChange={(e) => setMaxDifficulty(parseInt(e.target.value))}
                className="px-2 py-1.5 rounded border bg-background text-foreground text-sm"
              >
                {[1,2,3,4,5,6,7,8].map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <button
              onClick={fetchDebugData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              刷新数据
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg">
            {error}
          </div>
        )}

        {/* Fusion Weights Visualization */}
        {debugData && (
          <div className="bg-card rounded-xl border p-4">
            <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <PieChart className="w-5 h-5 text-primary" />
              融合权重分配
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {(debugData.fusion_weights.behavior * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">行为特征匹配</div>
                <div className="text-xs text-muted-foreground mt-1">做题习惯、正确率、速度</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                  {(debugData.fusion_weights.embedding * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">Embedding相似度</div>
                <div className="text-xs text-muted-foreground mt-1">语义匹配、擅长方向</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {(debugData.fusion_weights.difficulty * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">难度匹配(ZPD)</div>
                <div className="text-xs text-muted-foreground mt-1">最近发展区理论</div>
              </div>
            </div>
          </div>
        )}

        {/* System Status */}
        {debugData && (
          <div className="bg-card rounded-xl border overflow-hidden">
            <button
              onClick={() => toggleSection('systemStatus')}
              className="w-full p-4 flex items-center justify-between hover:bg-muted/50"
            >
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <Database className="w-5 h-5 text-primary" />
                系统状态
              </h3>
              {expandedSections.systemStatus ? <ChevronUp /> : <ChevronDown />}
            </button>
            {expandedSections.systemStatus && (
              <div className="p-4 pt-0 space-y-3">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="text-2xl font-bold text-foreground">
                      {debugData.system_status.total_exercises}
                    </div>
                    <div className="text-sm text-muted-foreground">总题目数</div>
                  </div>
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="text-2xl font-bold text-foreground">
                      {debugData.system_status.exercises_with_embedding}
                    </div>
                    <div className="text-sm text-muted-foreground">已生成Embedding</div>
                  </div>
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="text-2xl font-bold text-foreground">
                      {debugData.system_status.embedding_coverage}
                    </div>
                    <div className="text-sm text-muted-foreground">覆盖率</div>
                  </div>
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="flex items-center gap-2">
                      {debugData.system_status.embedding_service_configured ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                      <span className="text-sm text-foreground">
                        {debugData.system_status.embedding_service_configured ? '已配置' : '未配置'}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground">Embedding服务</div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="px-2 py-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded text-sm">
                    Provider: {debugData.system_status.embedding_provider}
                  </span>
                  <span className="px-2 py-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded text-sm">
                    Model: {debugData.system_status.embedding_model}
                  </span>
                </div>
                <button
                  onClick={batchUpdateEmbeddings}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80"
                >
                  <Zap className="w-4 h-4" />
                  批量生成Embedding (20题)
                </button>
              </div>
            )}
          </div>
        )}

        {/* User Stats */}
        {debugData && (
          <div className="bg-card rounded-xl border overflow-hidden">
            <button
              onClick={() => toggleSection('userStats')}
              className="w-full p-4 flex items-center justify-between hover:bg-muted/50"
            >
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                用户画像统计
              </h3>
              {expandedSections.userStats ? <ChevronUp /> : <ChevronDown />}
            </button>
            {expandedSections.userStats && (
              <div className="p-4 pt-0 space-y-3">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="text-2xl font-bold text-foreground">
                      {(debugData.user_stats.accuracy * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-muted-foreground">正确率</div>
                  </div>
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="text-2xl font-bold text-foreground">
                      {(debugData.user_stats.avg_attempts ?? debugData.user_stats.avg_time_spent ?? 0).toFixed(1)}次
                    </div>
                    <div className="text-sm text-muted-foreground">平均尝试次数</div>
                  </div>
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="text-2xl font-bold text-foreground">
                      {debugData.user_stats.completed_exercises}/{debugData.user_stats.total_exercises}
                    </div>
                    <div className="text-sm text-muted-foreground">已完成/总题数</div>
                  </div>
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="text-2xl font-bold text-foreground">
                      {debugData.user_stats.total_submissions}
                    </div>
                    <div className="text-sm text-muted-foreground">总提交次数</div>
                  </div>
                  <div className="bg-muted/30 rounded-lg p-3">
                    <div className="text-2xl font-bold text-foreground">
                      {getTierDisplay(debugData.user_stats.tier, debugData.user_stats.sub_tier)}
                    </div>
                    <div className="text-sm text-muted-foreground">当前段位</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {debugData.user_stats.stars} 颗星
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">行为Embedding:</span>
                  {debugData.user_stats.behavior_embedding ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                  <span className="text-sm text-foreground">
                    {debugData.user_stats.behavior_embedding
                      ? `${debugData.user_stats.behavior_embedding.length}维向量`
                      : '未生成'}
                  </span>
                </div>
                <button
                  onClick={recalculateProfile}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80"
                >
                  <RefreshCw className="w-4 h-4" />
                  重新计算画像Embedding
                </button>
              </div>
            )}
          </div>
        )}

        {/* Recommendations */}
        {debugData && debugData.recommendations.length > 0 && (
          <div className="bg-card rounded-xl border overflow-hidden">
            <button
              onClick={() => toggleSection('recommendations')}
              className="w-full p-4 flex items-center justify-between hover:bg-muted/50"
            >
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                推荐结果 (Top {debugData.recommendations.length})
              </h3>
              {expandedSections.recommendations ? <ChevronUp /> : <ChevronDown />}
            </button>
            {expandedSections.recommendations && (
              <div className="p-4 pt-0 space-y-3">
                {debugData.recommendations.map((rec, index) => (
                  <div
                    key={rec.exercise_id}
                    className="bg-muted/30 rounded-lg p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-primary text-white text-sm flex items-center justify-center">
                          {index + 1}
                        </span>
                        <span className="font-medium text-foreground">
                          {rec.title || `题目 ${rec.exercise_id}`}
                        </span>
                        <span className="px-2 py-0.5 bg-primary/10 text-primary rounded text-xs">
                          难度 {rec.difficulty}
                        </span>
                      </div>
                      <div className={`text-lg font-bold ${getScoreColor(rec.final_score)}`}>
                        {rec.final_score.toFixed(3)}
                      </div>
                    </div>

                    {/* Score Breakdown */}
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div className="bg-blue-100 dark:bg-blue-900/30 rounded p-2 text-center">
                        <div className="font-bold text-blue-600 dark:text-blue-400">
                          {rec.score_breakdown.behavior.toFixed(3)}
                        </div>
                        <div className="text-xs text-muted-foreground">行为分</div>
                      </div>
                      <div className="bg-purple-100 dark:bg-purple-900/30 rounded p-2 text-center">
                        <div className="font-bold text-purple-600 dark:text-purple-400">
                          {rec.score_breakdown.embedding.toFixed(3)}
                        </div>
                        <div className="text-xs text-muted-foreground">Embedding分</div>
                      </div>
                      <div className="bg-green-100 dark:bg-green-900/30 rounded p-2 text-center">
                        <div className="font-bold text-green-600 dark:text-green-400">
                          {rec.score_breakdown.difficulty.toFixed(3)}
                        </div>
                        <div className="text-xs text-muted-foreground">难度分</div>
                      </div>
                    </div>

                    {/* Reasons */}
                    <div className="flex flex-wrap gap-2">
                      {rec.reasons.map((reason, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-secondary/50 text-secondary-foreground rounded text-xs"
                        >
                          {reason}
                        </span>
                      ))}
                    </div>

                    {/* Knowledge Points */}
                    {rec.knowledge_points.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {rec.knowledge_points.map((kp, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-muted text-muted-foreground rounded text-xs"
                          >
                            {kp}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Algorithm Explanation */}
        <div className="bg-card rounded-xl border p-4">
          <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            算法说明
          </h3>
          <div className="space-y-3 text-sm text-muted-foreground">
            <p>
              <strong className="text-foreground">行为特征匹配 (40%)</strong>：
              根据用户历史行为调整推荐。高正确率用户推荐有挑战的题，
              低正确率用户推荐基础题巩固；尝试次数少说明学得快，推荐有深度的题，
              尝试次数多说明需要巩固，推荐基础题。
            </p>
            <p>
              <strong className="text-foreground">Embedding相似度 (35%)</strong>：
              计算用户画像向量与题目标签向量的余弦相似度。
              用户向量 = 做对题embedding × 0.6 - 做错题embedding × 0.4。
            </p>
            <p>
              <strong className="text-foreground">难度匹配 (25%)</strong>：
              基于ZPD（最近发展区）理论，推荐难度略高于用户当前水平的题目。
              目标难度 = 用户等级 + 0.5。
            </p>
            <div className="bg-muted/50 rounded-lg p-3 font-mono text-xs">
              final_score = 0.40 × behavior_score + 0.35 × embedding_score + 0.25 × difficulty_score
            </div>
          </div>
        </div>

        {/* Test Actions */}
        <div className="bg-card rounded-xl border p-4">
          <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
            <Play className="w-5 h-5 text-primary" />
            快速测试操作
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <button
              onClick={() => router.push('/arena/1')}
              className="flex flex-col items-center gap-2 p-4 bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors"
            >
              <Target className="w-6 h-6 text-primary" />
              <span className="text-sm text-foreground">进入挑战之路</span>
              <span className="text-xs text-muted-foreground">做几道题生成数据</span>
            </button>
            <button
              onClick={fetchDebugData}
              disabled={loading}
              className="flex flex-col items-center gap-2 p-4 bg-secondary/50 hover:bg-secondary rounded-lg transition-colors"
            >
              <RefreshCw className={`w-6 h-6 ${loading ? 'animate-spin' : ''}`} />
              <span className="text-sm text-foreground">刷新推荐</span>
              <span className="text-xs text-muted-foreground">查看最新推荐结果</span>
            </button>
            <button
              onClick={recalculateProfile}
              disabled={loading}
              className="flex flex-col items-center gap-2 p-4 bg-secondary/50 hover:bg-secondary rounded-lg transition-colors"
            >
              <Brain className="w-6 h-6" />
              <span className="text-sm text-foreground">重建画像</span>
              <span className="text-xs text-muted-foreground">从历史数据重建Embedding</span>
            </button>
            <button
              onClick={batchUpdateEmbeddings}
              disabled={loading}
              className="flex flex-col items-center gap-2 p-4 bg-secondary/50 hover:bg-secondary rounded-lg transition-colors"
            >
              <Database className="w-6 h-6" />
              <span className="text-sm text-foreground">生成Embedding</span>
              <span className="text-xs text-muted-foreground">为题目生成向量</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
