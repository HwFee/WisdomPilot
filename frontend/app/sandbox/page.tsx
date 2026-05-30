'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Gem, Gift, Calendar, Target, Swords,
  CheckCircle, XCircle, Loader2, RefreshCw,
  TrendingUp, TrendingDown, History, Lightbulb, Sparkles, BookOpen,
  Play, Shield, TestTube, ArrowLeft, Clock
} from 'lucide-react'
import { getStoredToken } from '@/lib/api'

interface CoreBalance {
  balance: number
  total_earned: number
  total_spent: number
}

interface TestQuestion {
  id: number
  question: string
  options: string[]
  correct_answer: string
  difficulty: number
  knowledge_point: string
}

interface TestResult {
  success: boolean
  message: string
  data?: Record<string, unknown>
}

export default function SandboxPage() {
  const { push, back } = useRouter()
  const [loading, setLoading] = useState<string | null>(null)
  const [balance, setBalance] = useState<CoreBalance | null>(null)
  const [testState, setTestState] = useState({
    results: [] as TestResult[],
    questions: [] as TestQuestion[],
    answers: {} as Record<number, string>,
  })
  const { results: testResults, questions: testQuestions, answers: userAnswers } = testState
  const [username, setUsername] = useState<string>('')

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // 获取测试题目
  const fetchTestQuestions = async (token: string) => {
    try {
      const res = await fetch(`${API_URL}/api/test/mastery/questions`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setTestState(prev => ({ ...prev, questions: data.questions || [] }))
      }
    } catch { /* ignore */ }
  }

  const fetchData = async () => {
    const token = getStoredToken()
    if (!token) return

    const balanceRes = await fetch(`${API_URL}/api/cores/balance`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (balanceRes.ok) setBalance(await balanceRes.json())
  }

  // 初始化
  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      push('/login')
      return
    }

    // 获取用户名
    try {
      const stored = localStorage.getItem('user:v1')
      if (stored) {
        const user = JSON.parse(stored)
        setUsername(user.username || '')
      }
    } catch { /* ignore */ }

    // 获取余额和测试题目
    fetchData()
    fetchTestQuestions(token)
  }, [push, back])

  const addResult = (success: boolean, message: string, data?: Record<string, unknown>) => {
    setTestState(prev => ({ ...prev, results: [{ success, message, data }, ...prev.results].slice(0, 10) }))
  }

  // 沙箱签到
  const testCheckin = async () => {
    const token = getStoredToken()
    if (!token) return

    setLoading('checkin')
    try {
      const res = await fetch(`${API_URL}/api/test/checkin`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      addResult(res.ok, res.ok ? `✅ 沙箱签到 +${data.cores_earned}智核，余额: ${data.balance_after}` : `❌ 失败: ${data.error || data.detail}`, data)
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch {
      addResult(false, `❌ 请求失败`)
    } finally {
      setLoading(null)
    }
  }

  // 沙箱精进之路提交
  const testMasterySubmit = async () => {
    const token = getStoredToken()
    if (!token) return

    setLoading('mastery')
    try {
      const answers = testQuestions.map(q => ({
        question_id: q.id,
        user_answer: userAnswers[q.id] || 'A'
      }))

      const res = await fetch(`${API_URL}/api/test/mastery/submit`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(answers)
      })
      const data = await res.json()
      addResult(res.ok, res.ok ? `✅ 精进之路答题完成！正确 ${data.correct_count}/${data.total} 题，+${data.cores_earned} 智核` : `❌ 失败: ${data.detail}`, data)
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch {
      addResult(false, `❌ 请求失败`)
    } finally {
      setLoading(null)
    }
  }

  // 沙箱挑战之路提交
  const testArenaSubmit = async (passed: boolean) => {
    const token = getStoredToken()
    if (!token) return

    setLoading('arena')
    try {
      const res = await fetch(`${API_URL}/api/test/arena/submit?exercise_id=101&passed=${passed}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      addResult(res.ok, res.ok ? `✅ 挑战之路答题${passed ? '正确' : '错误'}，+${data.cores_earned} 智核` : `❌ 失败: ${data.error || data.detail}`, data)
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch {
      addResult(false, `❌ 请求失败`)
    } finally {
      setLoading(null)
    }
  }

  // 沙箱AI提示
  const testAIHint = async (level: 'light' | 'medium' | 'deep') => {
    const token = getStoredToken()
    if (!token) return

    setLoading(`hint_${level}`)
    try {
      const res = await fetch(`${API_URL}/api/test/ai-hint/${level}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      addResult(res.ok, res.ok ? `✅ AI提示消耗 -${data.cost} 智核\n${data.hint}` : `❌ 失败: ${data.error}`, data)
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch {
      addResult(false, `❌ 请求失败`)
    } finally {
      setLoading(null)
    }
  }

  // 沙箱学习时长
  const testStudyTime = async (minutes: number) => {
    const token = getStoredToken()
    if (!token) return

    setLoading('studyTime')
    try {
      const res = await fetch(`${API_URL}/api/test/study-time?minutes=${minutes}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      addResult(res.ok, res.ok ? `✅ 学习${minutes}分钟 +${data.cores_earned} 智核` : `❌ 失败`, data)
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch {
      addResult(false, `❌ 请求失败`)
    } finally {
      setLoading(null)
    }
  }

  // 沙箱每日练习
  const testDailyExercises = async (completed: number) => {
    const token = getStoredToken()
    if (!token) return

    setLoading('dailyExercises')
    try {
      const res = await fetch(`${API_URL}/api/test/daily-exercises?completed=${completed}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      addResult(res.ok, res.ok ? `✅ 完成${completed}题 +${data.cores_earned} 智核` : `❌ 失败`, data)
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch {
      addResult(false, `❌ 请求失败`)
    } finally {
      setLoading(null)
    }
  }

  // 沙箱正确率
  const testDailyAccuracy = async (accuracy: number) => {
    const token = getStoredToken()
    if (!token) return

    setLoading('dailyAccuracy')
    try {
      const res = await fetch(`${API_URL}/api/test/daily-accuracy?accuracy=${accuracy}&total_questions=20`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      addResult(res.ok, res.ok ? `✅ 正确率${accuracy}% +${data.cores_earned} 智核` : `❌ 失败`, data)
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch {
      addResult(false, `❌ 请求失败`)
    } finally {
      setLoading(null)
    }
  }

  // 沙箱系统奖励
  const testBonus = async (amount: number) => {
    const token = getStoredToken()
    if (!token) return

    setLoading('bonus')
    try {
      const res = await fetch(`${API_URL}/api/test/bonus?amount=${amount}&reason=测试奖励`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      addResult(res.ok, res.ok ? `✅ 系统奖励 +${data.cores_earned} 智核` : `❌ 失败`, data)
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch {
      addResult(false, `❌ 请求失败`)
    } finally {
      setLoading(null)
    }
  }

  const handleGoBack = () => {
    if (window.history.length > 1 && document.referrer) {
      back()
    } else {
      push('/dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <button type="button" onClick={handleGoBack} className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
            <ArrowLeft className="size-5" />
            <span className="font-medium">沙箱测试</span>
          </button>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">{username}</span>
            <button type="button" onClick={fetchData} disabled={loading !== null}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50">
              <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 flex flex-col gap-y-6">
        {/* Sandbox Info */}
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg flex items-start gap-3">
          <Shield className="size-5 text-green-500 mt-0.5" />
          <div className="text-sm">
            <div className="font-medium text-green-600 dark:text-green-400 mb-1">沙箱模式说明</div>
            <ul className="text-muted-foreground space-y-1">
              <li>✅ 真实消耗/获得智核</li>
              <li>❌ 不计入今日做题数</li>
              <li>❌ 不影响正确率</li>
              <li>❌ 不改变段位/星星</li>
              <li>❌ 不解锁章节进度</li>
            </ul>
          </div>
        </div>

        {/* Balance */}
        <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 rounded-2xl border border-purple-500/30 p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-purple-400 mb-1">当前智核余额</div>
              <div className="text-4xl font-bold text-foreground flex items-center gap-2">
                <Gem className="size-8 text-purple-500" />
                {balance?.balance ?? 0}
              </div>
            </div>
            <div className="flex gap-6">
              <div className="text-center">
                <div className="flex items-center gap-1 text-green-500">
                  <TrendingUp className="size-4" />
                  <span className="font-bold">{balance?.total_earned ?? 0}</span>
                </div>
                <div className="text-xs text-muted-foreground">累计获得</div>
              </div>
              <div className="text-center">
                <div className="flex items-center gap-1 text-red-500">
                  <TrendingDown className="size-4" />
                  <span className="font-bold">{balance?.total_spent ?? 0}</span>
                </div>
                <div className="text-xs text-muted-foreground">累计消耗</div>
              </div>
            </div>
          </div>
        </div>

        {/* Earn Tests */}
        <div className="bg-card rounded-xl border p-4">
          <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Gift className="size-5 text-green-500" />
            获取智核测试
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <button type="button" onClick={testCheckin} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-green-500/10 hover:bg-green-500/20 rounded-lg border border-green-500/30 disabled:opacity-50">
              {loading === 'checkin' ? <Loader2 className="size-5 text-green-500 animate-spin" /> : <Calendar className="size-5 text-green-500" />}
              <span className="text-sm font-medium">签到</span>
              <span className="text-xs text-muted-foreground">+5 智核</span>
            </button>

            <button type="button" onClick={() => testArenaSubmit(true)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-blue-500/10 hover:bg-blue-500/20 rounded-lg border border-blue-500/30 disabled:opacity-50">
              {loading === 'arena' ? <Loader2 className="size-5 text-blue-500 animate-spin" /> : <Swords className="size-5 text-blue-500" />}
              <span className="text-sm font-medium">挑战正确</span>
              <span className="text-xs text-muted-foreground">+3 智核</span>
            </button>

            <button type="button" onClick={() => testStudyTime(30)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-cyan-500/10 hover:bg-cyan-500/20 rounded-lg border border-cyan-500/30 disabled:opacity-50">
              {loading === 'studyTime' ? <Loader2 className="size-5 text-cyan-500 animate-spin" /> : <span className="text-lg">⏱️</span>}
              <span className="text-sm font-medium">学习30分钟</span>
              <span className="text-xs text-muted-foreground">+5 智核</span>
            </button>

            <button type="button" onClick={() => testDailyExercises(20)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-teal-500/10 hover:bg-teal-500/20 rounded-lg border border-teal-500/30 disabled:opacity-50">
              {loading === 'dailyExercises' ? <Loader2 className="size-5 text-teal-500 animate-spin" /> : <span className="text-lg">📝</span>}
              <span className="text-sm font-medium">每日练习20题</span>
              <span className="text-xs text-muted-foreground">+5 智核</span>
            </button>

            <button type="button" onClick={() => testDailyAccuracy(80)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-orange-500/10 hover:bg-orange-500/20 rounded-lg border border-orange-500/30 disabled:opacity-50">
              {loading === 'dailyAccuracy' ? <Loader2 className="size-5 text-orange-500 animate-spin" /> : <span className="text-lg">🎯</span>}
              <span className="text-sm font-medium">正确率80%</span>
              <span className="text-xs text-muted-foreground">+5 智核</span>
            </button>

            <button type="button" onClick={() => testBonus(10)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-pink-500/10 hover:bg-pink-500/20 rounded-lg border border-pink-500/30 disabled:opacity-50">
              {loading === 'bonus' ? <Loader2 className="size-5 text-pink-500 animate-spin" /> : <span className="text-lg">🎁</span>}
              <span className="text-sm font-medium">系统奖励</span>
              <span className="text-xs text-muted-foreground">+10 智核</span>
            </button>
          </div>

          {/* Test Questions */}
          {testState.questions.length > 0 && (
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium">精进之路测试题</h3>
                <button type="button" onClick={testMasterySubmit} disabled={loading !== null}
                  className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50 flex items-center gap-2">
                  {loading === 'mastery' ? <Loader2 className="size-4 animate-spin" /> : <Target className="size-4" />}
                  提交答案
                </button>
              </div>
              <div className="flex flex-col gap-y-2">
                {testState.questions.slice(0, 2).map((q, idx) => (
                  <div key={q.id} className="p-3 bg-muted/30 rounded-lg text-sm">
                    <div className="font-medium mb-1">{idx + 1}. {q.question}</div>
                    <div className="flex flex-wrap gap-2">
                      {q.options.map((opt, i) => (
                        <button type="button" key={`${q.id}-opt-${opt}`} onClick={() => setTestState(prev => ({ ...prev, answers: { ...prev.answers, [q.id]: ['A', 'B', 'C', 'D'][i] } }))}
                          className={`px-2 py-1 text-xs rounded border ${testState.answers[q.id] === ['A', 'B', 'C', 'D'][i] ? 'bg-primary/20 border-primary' : 'bg-background'}`}>
                          {['A', 'B', 'C', 'D'][i]}. {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Spend Tests */}
        <div className="bg-card rounded-xl border p-4">
          <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Sparkles className="size-5 text-purple-500" />
            消耗智核测试（AI提示）
          </h2>
          <div className="grid grid-cols-3 gap-3">
            <button type="button" onClick={() => testAIHint('light')} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg border border-purple-500/30 disabled:opacity-50">
              {loading === 'hint_light' ? <Loader2 className="size-5 text-purple-400 animate-spin" /> : <Lightbulb className="size-5 text-purple-400" />}
              <span className="text-sm font-medium">轻度提示</span>
              <span className="text-xs text-muted-foreground">-1 智核</span>
            </button>

            <button type="button" onClick={() => testAIHint('medium')} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg border border-purple-500/30 disabled:opacity-50">
              {loading === 'hint_medium' ? <Loader2 className="size-5 text-purple-500 animate-spin" /> : <Sparkles className="size-5 text-purple-500" />}
              <span className="text-sm font-medium">中度提示</span>
              <span className="text-xs text-muted-foreground">-3 智核</span>
            </button>

            <button type="button" onClick={() => testAIHint('deep')} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg border border-purple-500/30 disabled:opacity-50">
              {loading === 'hint_deep' ? <Loader2 className="size-5 text-purple-600 animate-spin" /> : <BookOpen className="size-5 text-purple-600" />}
              <span className="text-sm font-medium">深度解析</span>
              <span className="text-xs text-muted-foreground">-5 智核</span>
            </button>
          </div>
        </div>

        {/* Test Results */}
        <div className="bg-card rounded-xl border p-4">
          <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Play className="size-5 text-blue-500" />
            测试结果
          </h2>
          {testState.results.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">点击上方按钮开始测试</div>
          ) : (
            <div className="flex flex-col gap-y-2">
              {testState.results.map((r, i) => (
                <div key={`result-${r.success}-${r.message?.slice(0, 30) || i}`} className={`p-3 rounded-lg ${r.success ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                  <div className="flex items-start gap-2">
                    {r.success ? <CheckCircle className="size-5 text-green-500" /> : <XCircle className="size-5 text-red-500" />}
                    <div className="flex-1 text-sm text-foreground whitespace-pre-wrap">{r.message}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
