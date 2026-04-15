'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import {
  X, Zap, CheckCircle, XCircle, ArrowRight, RotateCcw, Play,
  Swords, Clock, Trophy, TrendingUp, Crown, Medal, Target, ChevronRight
} from 'lucide-react'
import {
  getArenaProfile,
  startChallengeSession,
  submitChallengeSession,
  TIER_ICONS, TIER_NAMES
} from '@/lib/api'
import type { ArenaProfileResponse, ChallengeSessionResponse, ChallengeResultResponse, ChallengeExercise, Tier } from '@/types/api'

// Difficulty colors
const DIFFICULTY_COLORS: Record<number, string> = {
  1: 'bg-green-500/20 text-green-400 border-green-500/30',
  2: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  3: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  4: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  5: 'bg-red-500/20 text-red-400 border-red-500/30',
}

const DIFFICULTY_NAMES: Record<number, string> = {
  1: '入门',
  2: '基础',
  3: '中等',
  4: '困难',
  5: '极难',
}

const DIFFICULTY_TIME: Record<number, number> = {
  1: 60,
  2: 90,
  3: 120,
  4: 180,
  5: 300,
}

type ChallengeState = 'select' | 'in_progress' | 'result'

interface AnswerState {
  exerciseId: string
  answer: string
  isCorrect: boolean
  timeSpent: number
}

export default function ChallengePage() {
  const params = useParams()
  const router = useRouter()
  const courseId = parseInt(params.id as string)

  const [profile, setProfile] = useState<ArenaProfileResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [challengeState, setChallengeState] = useState<ChallengeState>('select')
  const [selectedDifficulty, setSelectedDifficulty] = useState<number>(3)
  const [session, setSession] = useState<ChallengeSessionResponse | null>(null)
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0)
  const [answers, setAnswers] = useState<AnswerState[]>([])
  const [answer, setAnswer] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const [isCorrect, setIsCorrect] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [result, setResult] = useState<ChallengeResultResponse | null>(null)
  const [sessionStartTime, setSessionStartTime] = useState<Date | null>(null)

  const fetchProfile = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        router.push('/login')
        return
      }

      const data = await getArenaProfile(courseId, token)
      setProfile(data)
    } catch (error) {
      console.error('Failed to fetch arena profile:', error)
    } finally {
      setLoading(false)
    }
  }, [courseId, router])

  useEffect(() => {
    fetchProfile()
  }, [fetchProfile])

  // Timer effect
  useEffect(() => {
    if (challengeState !== 'in_progress' || !session) return

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          // Time's up - auto submit
          handleSubmitChallenge()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [challengeState, session])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleStartChallenge = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      setLoading(true)
      const data = await startChallengeSession(courseId, {
        difficulty_level: selectedDifficulty,
        question_count: 10
      }, token)

      setSession(data)
      setChallengeState('in_progress')
      setTimeRemaining(data.time_limit)
      setSessionStartTime(new Date())
      setCurrentExerciseIndex(0)
      setAnswers([])
      setAnswer(null)
      setSubmitted(false)
    } catch (error) {
      console.error('Failed to start challenge:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitAnswer = () => {
    if (!answer || !session) return

    const currentExercise = session.exercises[currentExerciseIndex]
    // TODO: Backend should validate the answer
    // For now, simulate correctness based on answer selection
    // In production, this should be validated by backend API
    const correct = Math.random() > 0.4

    setIsCorrect(correct)
    setSubmitted(true)

    setAnswers(prev => [...prev, {
      exerciseId: currentExercise.id.toString(),
      answer,
      isCorrect: correct,
      timeSpent: 30 // Approximate
    }])
  }

  const handleNextExercise = () => {
    if (!session) return

    if (currentExerciseIndex < session.exercises.length - 1) {
      setCurrentExerciseIndex(prev => prev + 1)
      setAnswer(null)
      setSubmitted(false)
    } else {
      // All exercises done - submit challenge
      handleSubmitChallenge()
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const handleSubmitChallenge = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token || !session) return

      setLoading(true)
      const totalTime = sessionStartTime
        ? Math.floor((new Date().getTime() - sessionStartTime.getTime()) / 1000)
        : session.time_limit

      const data = await submitChallengeSession(courseId, session.session_id, {
        answers: answers.map(a => ({
          exercise_id: a.exerciseId,
          answer: a.answer,
          is_correct: a.isCorrect,
          time_spent: a.timeSpent,
        })),
        total_time: totalTime
      }, token)

      setResult(data)
      setChallengeState('result')
    } catch (error) {
      console.error('Failed to submit challenge:', error)
    } finally {
      setLoading(false)
    }
  }, [session, sessionStartTime, courseId, answers])

  const handleBackToSelect = () => {
    setChallengeState('select')
    setSession(null)
    setResult(null)
    fetchProfile()
  }

  if (loading && !profile) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">加载中...</p>
        </div>
      </div>
    )
  }

  // Result State
  if (challengeState === 'result' && result) {
    const passed = result.correct_answers >= result.total_questions * 0.8
    const accuracy = Math.round((result.correct_answers / result.total_questions) * 100)

    return (
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <Link href={`/courses/${courseId}`} className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
              <X className="w-4 h-4" />
              <span className="text-sm">退出</span>
            </Link>
            <div className="flex items-center gap-2">
              <Swords className="w-5 h-5 text-blue-500" />
              <span className="font-semibold">挑战结果</span>
            </div>
            <div className="w-20"></div>
          </div>
        </header>

        <main className="pt-24 pb-12 px-4">
          <div className="max-w-md mx-auto">
            {/* Result Card */}
            <div className={`rounded-2xl border p-8 text-center mb-6 ${
              passed
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}>
              {passed ? (
                <CheckCircle className="w-20 h-20 text-emerald-500 mx-auto mb-4" />
              ) : (
                <XCircle className="w-20 h-20 text-red-400 mx-auto mb-4" />
              )}

              <h2 className="text-2xl font-bold text-foreground mb-2">
                {passed ? '挑战成功！' : '挑战失败'}
              </h2>

              <p className="text-muted-foreground mb-6">
                答对 {result.correct_answers}/{result.total_questions} 题 ({accuracy}%)
              </p>

              {/* Score breakdown */}
              <div className="bg-card rounded-xl p-4 mb-6 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">基础分</span>
                  <span className="font-medium text-foreground">{result.base_score.toFixed(0)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">时间奖励</span>
                  <span className="font-medium text-blue-500">+{result.time_bonus.toFixed(0)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">连胜奖励</span>
                  <span className="font-medium text-yellow-500">+{result.streak_bonus.toFixed(0)}</span>
                </div>
                <div className="border-t border-border pt-3 flex justify-between">
                  <span className="font-medium text-foreground">最终得分</span>
                  <span className="text-xl font-bold text-primary">{result.final_score.toFixed(0)}</span>
                </div>
              </div>

              {/* Tier change */}
              {result.new_tier && (
                <div className="bg-yellow-500/10 rounded-xl p-4 mb-6 border border-yellow-500/20">
                  <p className="text-sm text-yellow-600 mb-2">段位晋升！</p>
                  <div className="flex items-center justify-center gap-3">
                    <span className="text-3xl">{TIER_ICONS[result.tier]}</span>
                    <ArrowRight className="w-5 h-5 text-yellow-500" />
                    <span className="text-3xl">{TIER_ICONS[result.new_tier]}</span>
                  </div>
                  <p className="text-sm font-medium text-foreground mt-2">
                    {TIER_NAMES[result.tier]} → {TIER_NAMES[result.new_tier]}
                  </p>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={handleBackToSelect}
                className="flex-1 py-3 bg-card border border-border rounded-xl font-medium text-foreground hover:bg-muted transition-colors"
              >
                返回选择
              </button>
              <button
                onClick={handleStartChallenge}
                className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-blue-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all"
              >
                再来一局
              </button>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // In Progress State
  if (challengeState === 'in_progress' && session) {
    const currentExercise = session.exercises[currentExerciseIndex]
    const isLastExercise = currentExerciseIndex === session.exercises.length - 1
    const correctCount = answers.filter(a => a.isCorrect).length

    return (
      <div className="min-h-screen bg-background">
        {/* Header with timer */}
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
          <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
            <button
              onClick={() => setChallengeState('select')}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="w-4 h-4" />
              <span className="text-sm">退出</span>
            </button>

            <div className="flex items-center gap-4">
              {/* Progress */}
              <div className="flex items-center gap-1">
                {session.exercises.map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      i < currentExerciseIndex
                        ? answers[i]?.isCorrect ? 'bg-emerald-400' : 'bg-red-400'
                        : i === currentExerciseIndex
                          ? submitted
                            ? isCorrect ? 'bg-emerald-400' : 'bg-red-400'
                            : 'bg-primary'
                          : 'bg-muted'
                    }`}
                  />
                ))}
              </div>

              {/* Timer */}
              <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full ${
                timeRemaining < 60 ? 'bg-red-500/20 text-red-400' : 'bg-muted text-foreground'
              }`}>
                <Clock className="w-4 h-4" />
                <span className="font-mono font-medium">{formatTime(timeRemaining)}</span>
              </div>
            </div>

            {/* Score */}
            <div className="flex items-center gap-1.5 px-3 py-1 bg-blue-500/10 rounded-full">
              <Trophy className="w-4 h-4 text-blue-500" />
              <span className="font-medium text-blue-500">{correctCount}/{session.exercises.length}</span>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="pt-20 pb-24 px-4">
          <div className="max-w-2xl mx-auto">
            {/* Question header */}
            <div className="flex items-center gap-3 mb-6">
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm font-medium">
                {currentExerciseIndex + 1} / {session.exercises.length}
              </span>
              <span className={`px-3 py-1 rounded-lg text-xs font-medium border ${DIFFICULTY_COLORS[currentExercise.difficulty]}`}>
                {DIFFICULTY_NAMES[currentExercise.difficulty]}
              </span>
              <span className="text-xs text-muted-foreground">
                {session.score_multiplier}x 积分
              </span>
            </div>

            {/* Question */}
            <div className="bg-card rounded-2xl border border-border p-6 mb-6">
              <h2 className="text-xl font-bold text-foreground mb-4">
                {currentExercise.content?.text || currentExercise.title}
              </h2>

              {/* Knowledge points */}
              {currentExercise.knowledge_points.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {currentExercise.knowledge_points.map((kp, i) => (
                    <span key={i} className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                      {kp}
                    </span>
                  ))}
                </div>
              )}

              {/* Programming question: show code template and test cases */}
              {currentExercise.type === 'programming' && currentExercise.content?.code_template && (
                <div className="mb-4">
                  <p className="text-sm text-muted-foreground mb-2">代码模板：</p>
                  <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm font-mono">
                    {currentExercise.content.code_template}
                  </pre>
                </div>
              )}

              {/* Test cases for programming questions */}
              {currentExercise.type === 'programming' && currentExercise.test_cases && currentExercise.test_cases.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm text-muted-foreground mb-2">测试用例：</p>
                  <div className="space-y-2">
                    {currentExercise.test_cases.map((tc: { input: string; expected: string }, i: number) => (
                      <div key={i} className="bg-muted rounded-lg p-3 text-sm font-mono">
                        <span className="text-muted-foreground">输入: </span>
                        <span className="text-foreground">{tc.input}</span>
                        <span className="text-muted-foreground ml-4">期望: </span>
                        <span className="text-green-500">{tc.expected}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Choice question hint */}
              {currentExercise.type !== 'programming' && currentExercise.content?.options && (
                <p className="text-muted-foreground text-sm">
                  点击下方选项选择答案...
                </p>
              )}
            </div>

            {/* Options - for choice questions */}
            {currentExercise.type !== 'programming' && currentExercise.content?.options && (
              <div className="space-y-3">
                {currentExercise.content.options.map((opt: string, i: number) => {
                  const optLabel = String.fromCharCode(65 + i) // A, B, C, D
                  return (
                    <button
                      key={optLabel}
                      onClick={() => !submitted && setAnswer(optLabel)}
                      disabled={submitted}
                      className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                        submitted
                          ? answer === optLabel
                            ? isCorrect
                              ? 'border-emerald-500 bg-emerald-500/10'
                              : 'border-red-500 bg-red-500/10'
                            : 'border-border opacity-50'
                          : answer === optLabel
                            ? 'border-primary bg-primary/10'
                            : 'border-border hover:border-muted hover:bg-muted/30'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium ${
                          answer === optLabel && !submitted ? 'bg-primary text-primary-foreground' :
                          submitted && answer === optLabel && isCorrect ? 'bg-emerald-500 text-white' :
                          submitted && answer === optLabel && !isCorrect ? 'bg-red-500 text-white' :
                          'bg-muted text-muted-foreground'
                        }`}>
                          {optLabel}
                        </span>
                        <span className="text-foreground">{opt}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}

            {/* Programming question: show open editor button */}
            {currentExercise.type === 'programming' && (
              <div className="text-center py-4">
                <button
                  className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  打开编辑器
                </button>
              </div>
            )}
          </div>
        </main>

        {/* Bottom action bar */}
        <div className={`fixed bottom-0 left-0 right-0 border-t transition-colors ${
          submitted
            ? isCorrect ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/20'
            : 'bg-card border-border'
        }`}>
          <div className="max-w-2xl mx-auto px-4 py-4">
            {submitted ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {isCorrect ? (
                    <>
                      <CheckCircle className="w-6 h-6 text-emerald-500" />
                      <span className="font-medium text-emerald-500">正确！</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-6 h-6 text-red-400" />
                      <span className="font-medium text-red-400">错误</span>
                    </>
                  )}
                </div>
                <button
                  onClick={handleNextExercise}
                  className="px-8 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
                >
                  {isLastExercise ? '完成挑战' : '下一题'}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={handleSubmitAnswer}
                disabled={!answer}
                className="w-full py-4 bg-gradient-to-r from-blue-500 to-blue-400 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                提交答案
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Select State (default)
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href={`/courses/${courseId}`} className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
            <span className="text-sm">返回</span>
          </Link>
          <div className="flex items-center gap-2">
            <Swords className="w-5 h-5 text-blue-500" />
            <span className="font-semibold">挑战之路</span>
          </div>
          <div className="w-20"></div>
        </div>
      </header>

      <main className="pt-20 pb-12 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Profile Card */}
          {profile && (
            <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-2xl border border-blue-500/20 p-6 mb-8">
              <div className="flex items-center gap-4">
                <div className="text-5xl">{TIER_ICONS[profile.tier]}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-2xl font-bold text-foreground">{TIER_NAMES[profile.tier]}</span>
                    {profile.rank && (
                      <span className="text-sm text-muted-foreground"># {profile.rank}</span>
                    )}
                  </div>
                  <p className="text-muted-foreground mb-2">
                    总积分 <span className="font-bold text-blue-500">{profile.total_score.toFixed(0)}</span>
                  </p>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-4 h-4" />
                      {profile.total_challenges} 场挑战
                    </span>
                    <span>{profile.wins} 胜</span>
                    {profile.best_streak > 0 && (
                      <span>最高连胜 {profile.best_streak}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Difficulty Selection */}
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            选择难度
          </h2>

          <div className="grid gap-3 mb-8">
            {[1, 2, 3, 4, 5].map((level) => (
              <button
                key={level}
                onClick={() => setSelectedDifficulty(level)}
                className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                  selectedDifficulty === level
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-muted hover:bg-muted/30'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-lg text-sm font-medium border ${DIFFICULTY_COLORS[level]}`}>
                      {DIFFICULTY_NAMES[level]}
                    </span>
                    <div className="text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {DIFFICULTY_TIME[level]}秒/题
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-foreground">
                      {level === 1 ? '1.0x' : level === 2 ? '1.2x' : level === 3 ? '1.5x' : level === 4 ? '2.0x' : '3.0x'}
                    </span>
                    <span className="text-xs text-muted-foreground ml-1">积分</span>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Start Button */}
          <button
            onClick={handleStartChallenge}
            className="w-full py-4 bg-gradient-to-r from-blue-500 to-blue-400 text-white rounded-xl font-semibold text-lg hover:shadow-lg hover:shadow-blue-500/25 transition-all inline-flex items-center justify-center gap-2"
          >
            <Play className="w-5 h-5" />
            开始挑战
            <ArrowRight className="w-5 h-5" />
          </button>

          {/* Info */}
          <div className="mt-6 text-center text-sm text-muted-foreground">
            <p>完成挑战可获得积分，积分越高段位越高</p>
            <p className="mt-1">连续答对可获得连胜奖励</p>
          </div>
        </div>
      </main>
    </div>
  )
}
