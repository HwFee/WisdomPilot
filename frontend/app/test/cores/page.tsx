'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Gem, Gift, Calendar, Target, Swords,
  CheckCircle, XCircle, Loader2, RefreshCw,
  TrendingUp, TrendingDown, History, Lightbulb, Sparkles, BookOpen,
  Play, Shield, TestTube, Info, ExternalLink
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

export default function CoreTestPage() {
  const router = useRouter()
  const [loading, setLoading] = useState<string | null>(null)
  const [balance, setBalance] = useState<CoreBalance | null>(null)
  const [transactions, setTransactions] = useState<unknown[]>([])
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [testQuestions, setTestQuestions] = useState<TestQuestion[]>([])
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({})
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
        setTestQuestions(data.questions || [])
      }
    } catch { /* ignore */ }
  }

  // 初始化
  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      router.push('/login')
      return
    }

    // 获取用户名
    try {
      const stored = localStorage.getItem('user')
      if (stored) {
        const user = JSON.parse(stored)
        setUsername(user.username || '')
      }
    } catch { /* ignore */ }

    // 获取余额
    fetch(`${API_URL}/api/cores/balance`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : null)
      .then(setBalance)

    // 获取测试题目
    fetchTestQuestions(token)
  }, [router])

  const fetchData = async () => {
    const token = getStoredToken()
    if (!token) return

    const balanceRes = await fetch(`${API_URL}/api/cores/balance`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (balanceRes.ok) setBalance(await balanceRes.json())
  }

  const addResult = (success: boolean, message: string, data?: Record<string, unknown>) => {
    setTestResults(prev => [{ success, message, data }, ...prev].slice(0, 10))
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
    } catch (err) {
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
      // 构造答案
      const answers = testQuestions.map(q => ({
        question_id: q.id,
        user_answer: userAnswers[q.id] || 'A' // 默认选A
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
      addResult(
        res.ok,
        res.ok
          ? `✅ 精进之路答题完成！正确 ${data.correct_count}/${data.total} 题，+${data.cores_earned} 智核`
          : `❌ 失败: ${data.detail}`,
        data
      )
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch (err) {
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
      addResult(
        res.ok,
        res.ok
          ? `✅ 挑战之路答题${passed ? '正确' : '错误'}，+${data.cores_earned} 智核`
          : `❌ 失败: ${data.error || data.detail}`,
        data
      )
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch (err) {
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
      addResult(
        res.ok,
        res.ok
          ? `✅ AI提示消耗 -${data.cost} 智核\n${data.hint}`
          : `❌ 失败: ${data.error}`,
        data
      )
      if (res.ok) { fetchData(); setBalance({ ...balance!, balance: data.balance_after }) }
    } catch (err) {
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

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <TestTube className="w-7 h-7 text-purple-500" />
              智核系统沙箱测试
            </h1>
            <p className="text-muted-foreground mt-1">隔离测试环境，不影响真实统计数据</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/cores')}
              className="flex items-center gap-2 px-4 py-2 bg-purple-500/10 text-purple-600 rounded-lg hover:bg-purple-500/20 border border-purple-500/30"
            >
              <History className="w-4 h-4" />
              交易记录
              <ExternalLink className="w-3 h-3" />
            </button>
            <span className="text-sm text-muted-foreground">{username}</span>
            <button onClick={fetchData} disabled={loading !== null}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </button>
          </div>
        </div>

        {/* Sandbox Info */}
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg flex items-start gap-3">
          <Shield className="w-5 h-5 text-green-500 mt-0.5" />
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
                <Gem className="w-8 h-8 text-purple-500" />
                {balance?.balance ?? 0}
              </div>
            </div>
            <div className="flex gap-6">
              <div className="text-center">
                <div className="flex items-center gap-1 text-green-500">
                  <TrendingUp className="w-4 h-4" />
                  <span className="font-bold">{balance?.total_earned ?? 0}</span>
                </div>
                <div className="text-xs text-muted-foreground">累计获得</div>
              </div>
              <div className="text-center">
                <div className="flex items-center gap-1 text-red-500">
                  <TrendingDown className="w-4 h-4" />
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
            <Gift className="w-5 h-5 text-green-500" />
            获取智核测试
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <button onClick={testCheckin} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-green-500/10 hover:bg-green-500/20 rounded-lg border border-green-500/30 disabled:opacity-50">
              {loading === 'checkin' ? <Loader2 className="w-5 h-5 text-green-500 animate-spin" /> : <Calendar className="w-5 h-5 text-green-500" />}
              <span className="text-sm font-medium">签到</span>
              <span className="text-xs text-muted-foreground">+5 智核</span>
            </button>

            <button onClick={() => testArenaSubmit(true)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-blue-500/10 hover:bg-blue-500/20 rounded-lg border border-blue-500/30 disabled:opacity-50">
              {loading === 'arena' ? <Loader2 className="w-5 h-5 text-blue-500 animate-spin" /> : <Swords className="w-5 h-5 text-blue-500" />}
              <span className="text-sm font-medium">挑战正确</span>
              <span className="text-xs text-muted-foreground">+3 智核</span>
            </button>

            <button onClick={() => testArenaSubmit(false)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-gray-500/10 hover:bg-gray-500/20 rounded-lg border border-gray-500/30 disabled:opacity-50">
              {loading === 'arena' ? <Loader2 className="w-5 h-5 text-gray-500 animate-spin" /> : <XCircle className="w-5 h-5 text-gray-500" />}
              <span className="text-sm font-medium">挑战错误</span>
              <span className="text-xs text-muted-foreground">+0 智核</span>
            </button>

            <button onClick={() => testStudyTime(30)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-cyan-500/10 hover:bg-cyan-500/20 rounded-lg border border-cyan-500/30 disabled:opacity-50">
              {loading === 'studyTime' ? <Loader2 className="w-5 h-5 text-cyan-500 animate-spin" /> : <span className="text-lg">⏱️</span>}
              <span className="text-sm font-medium">学习30分钟</span>
              <span className="text-xs text-muted-foreground">+5 智核</span>
            </button>

            <button onClick={() => testStudyTime(60)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-cyan-500/10 hover:bg-cyan-500/20 rounded-lg border border-cyan-500/30 disabled:opacity-50">
              {loading === 'studyTime' ? <Loader2 className="w-5 h-5 text-cyan-500 animate-spin" /> : <span className="text-lg">⏱️</span>}
              <span className="text-sm font-medium">学习60分钟</span>
              <span className="text-xs text-muted-foreground">+10 智核</span>
            </button>

            <button onClick={() => testDailyExercises(20)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-teal-500/10 hover:bg-teal-500/20 rounded-lg border border-teal-500/30 disabled:opacity-50">
              {loading === 'dailyExercises' ? <Loader2 className="w-5 h-5 text-teal-500 animate-spin" /> : <span className="text-lg">📝</span>}
              <span className="text-sm font-medium">每日练习20题</span>
              <span className="text-xs text-muted-foreground">+5 智核</span>
            </button>

            <button onClick={() => testDailyExercises(30)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-teal-500/10 hover:bg-teal-500/20 rounded-lg border border-teal-500/30 disabled:opacity-50">
              {loading === 'dailyExercises' ? <Loader2 className="w-5 h-5 text-teal-500 animate-spin" /> : <span className="text-lg">📝</span>}
              <span className="text-sm font-medium">每日练习30题</span>
              <span className="text-xs text-muted-foreground">+10 智核</span>
            </button>

            <button onClick={() => testDailyAccuracy(80)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-orange-500/10 hover:bg-orange-500/20 rounded-lg border border-orange-500/30 disabled:opacity-50">
              {loading === 'dailyAccuracy' ? <Loader2 className="w-5 h-5 text-orange-500 animate-spin" /> : <span className="text-lg">🎯</span>}
              <span className="text-sm font-medium">正确率80%</span>
              <span className="text-xs text-muted-foreground">+5 智核</span>
            </button>

            <button onClick={() => testDailyAccuracy(90)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-orange-500/10 hover:bg-orange-500/20 rounded-lg border border-orange-500/30 disabled:opacity-50">
              {loading === 'dailyAccuracy' ? <Loader2 className="w-5 h-5 text-orange-500 animate-spin" /> : <span className="text-lg">🎯</span>}
              <span className="text-sm font-medium">正确率90%</span>
              <span className="text-xs text-muted-foreground">+10 智核</span>
            </button>

            <button onClick={() => testBonus(10)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-pink-500/10 hover:bg-pink-500/20 rounded-lg border border-pink-500/30 disabled:opacity-50">
              {loading === 'bonus' ? <Loader2 className="w-5 h-5 text-pink-500 animate-spin" /> : <span className="text-lg">🎁</span>}
              <span className="text-sm font-medium">系统奖励</span>
              <span className="text-xs text-muted-foreground">+10 智核</span>
            </button>

            <button onClick={() => testBonus(50)} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-pink-500/10 hover:bg-pink-500/20 rounded-lg border border-pink-500/30 disabled:opacity-50">
              {loading === 'bonus' ? <Loader2 className="w-5 h-5 text-pink-500 animate-spin" /> : <span className="text-lg">🎁</span>}
              <span className="text-sm font-medium">大额奖励</span>
              <span className="text-xs text-muted-foreground">+50 智核</span>
            </button>
          </div>

          {/* Test Questions - 精进之路答题 */}
          {testQuestions.length > 0 && (
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium">精进之路测试题（选择答案后点击提交）</h3>
                <button
                  onClick={testMasterySubmit}
                  disabled={loading !== null || testQuestions.length === 0}
                  className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading === 'mastery' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Target className="w-4 h-4" />
                  )}
                  提交答案 {testQuestions.length > 0 && `(+${testQuestions.filter(q => userAnswers[q.id]).length * 2}智核)`}
                </button>
              </div>
              <div className="space-y-3">
                {testQuestions.map((q, idx) => (
                  <div key={q.id} className="p-3 bg-muted/30 rounded-lg">
                    <div className="text-sm font-medium mb-2">
                      <span className="text-muted-foreground mr-2">{idx + 1}.</span>
                      {q.question}
                      {userAnswers[q.id] && (
                        <span className="ml-2 text-green-500 text-xs">已选: {userAnswers[q.id]}</span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {q.options.map((opt, i) => (
                        <button
                          key={i}
                          onClick={() => setUserAnswers({ ...userAnswers, [q.id]: ['A', 'B', 'C', 'D'][i] })}
                          className={`px-3 py-1 text-sm rounded border transition-colors ${
                            userAnswers[q.id] === ['A', 'B', 'C', 'D'][i]
                              ? 'bg-primary/20 border-primary text-primary font-medium'
                              : 'bg-background border-border hover:border-primary/50'
                          }`}
                        >
                          {['A', 'B', 'C', 'D'][i]}. {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 text-xs text-muted-foreground">
                💡 提示：正确答案每题+2智核，答错不扣分。当前已选择 {Object.keys(userAnswers).length}/{testQuestions.length} 题
              </div>
            </div>
          )}

          {/* 没有题目时的提示 */}
          {testQuestions.length === 0 && (
            <div className="border-t pt-4">
              <div className="text-center py-4 text-muted-foreground bg-muted/30 rounded-lg">
                <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>点击"精进之路"按钮加载测试题目</p>
                <p className="text-xs mt-1">或者后端服务未启动</p>
              </div>
            </div>
          )}
        </div>

        {/* Spend Tests */}
        <div className="bg-card rounded-xl border p-4">
          <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-500" />
            消耗智核测试（AI提示）
          </h2>
          <div className="grid grid-cols-3 gap-3">
            <button onClick={() => testAIHint('light')} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg border border-purple-500/30 disabled:opacity-50">
              {loading === 'hint_light' ? <Loader2 className="w-5 h-5 text-purple-400 animate-spin" /> : <Lightbulb className="w-5 h-5 text-purple-400" />}
              <span className="text-sm font-medium">轻度提示</span>
              <span className="text-xs text-muted-foreground">-1 智核</span>
            </button>

            <button onClick={() => testAIHint('medium')} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg border border-purple-500/30 disabled:opacity-50">
              {loading === 'hint_medium' ? <Loader2 className="w-5 h-5 text-purple-500 animate-spin" /> : <Sparkles className="w-5 h-5 text-purple-500" />}
              <span className="text-sm font-medium">中度提示</span>
              <span className="text-xs text-muted-foreground">-3 智核</span>
            </button>

            <button onClick={() => testAIHint('deep')} disabled={loading !== null}
              className="flex flex-col items-center gap-1 p-3 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg border border-purple-500/30 disabled:opacity-50">
              {loading === 'hint_deep' ? <Loader2 className="w-5 h-5 text-purple-600 animate-spin" /> : <BookOpen className="w-5 h-5 text-purple-600" />}
              <span className="text-sm font-medium">深度解析</span>
              <span className="text-xs text-muted-foreground">-5 智核</span>
            </button>
          </div>
        </div>

        {/* Test Results */}
        <div className="bg-card rounded-xl border p-4">
          <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Play className="w-5 h-5 text-blue-500" />
            测试结果
          </h2>
          {testResults.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">点击上方按钮开始测试</div>
          ) : (
            <div className="space-y-2">
              {testResults.map((r, i) => (
                <div key={i} className={`p-3 rounded-lg ${r.success ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                  <div className="flex items-start gap-2">
                    {r.success ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
                    <div className="flex-1">
                      <div className="text-sm text-foreground whitespace-pre-wrap">{r.message}</div>
                      {r.data && (
                        <details className="mt-1">
                          <summary className="text-xs text-muted-foreground cursor-pointer">查看详情</summary>
                          <pre className="mt-2 text-xs bg-muted/50 p-2 rounded overflow-auto max-h-40">{JSON.stringify(r.data, null, 2)}</pre>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* API Reference */}
        <div className="bg-card rounded-xl border p-4">
          <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Info className="w-5 h-5 text-blue-500" />
            沙箱API参考
          </h2>
          <div className="text-sm text-muted-foreground space-y-1 font-mono">
            <div>GET  /api/test/mastery/questions - 获取测试题目</div>
            <div>POST /api/test/mastery/submit - 提交精进之路答案</div>
            <div>GET  /api/test/arena/exercises - 获取挑战题目</div>
            <div>POST /api/test/arena/submit - 提交挑战答案</div>
            <div>POST /api/test/checkin - 测试签到</div>
            <div>POST /api/test/ai-hint/:level - AI提示</div>
          </div>
        </div>
      </div>
    </div>
  )
}
