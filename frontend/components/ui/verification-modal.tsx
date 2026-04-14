'use client'

import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, Clock, Trophy, Zap } from 'lucide-react'

interface VerificationQuestion {
  id: string
  type: 'choice' | 'programming' | 'fill_blank'
  difficulty: number
  content: {
    text: string
    options?: string[]
  }
  hints?: string[]
}

interface VerificationModalProps {
  isOpen: boolean
  onClose: () => void
  stageId: number
  onComplete: (result: VerificationResult) => void
}

interface VerificationResult {
  passed: boolean
  correct_count: number
  total_count: number
  xp_earned: number
  quota_bonus: number
}

export function VerificationModal({
  isOpen,
  onClose,
  stageId,
  onComplete
}: VerificationModalProps) {
  const [questions, setQuestions] = useState<VerificationQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<VerificationResult | null>(null)
  const [timeLeft, setTimeLeft] = useState(600) // 10 minutes
  const [started, setStarted] = useState(false)

  useEffect(() => {
    if (isOpen && !started) {
      fetchQuestions()
    }
  }, [isOpen, stageId])

  useEffect(() => {
    if (started && timeLeft > 0 && !result) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000)
      return () => clearTimeout(timer)
    } else if (timeLeft === 0 && !result) {
      handleSubmit()
    }
  }, [started, timeLeft, result])

  const fetchQuestions = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/stages/${stageId}/verify`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setQuestions(data.questions)
        setTimeLeft(data.time_limit || 600)
        setStarted(true)
      }
    } catch (error) {
      console.error('Failed to fetch verification questions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/stages/${stageId}/verify/submit`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ answers })
        }
      )

      if (response.ok) {
        const data = await response.json()
        setResult(data)
        onComplete(data)
      }
    } catch (error) {
      console.error('Failed to submit verification:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-2xl border border-border max-w-2xl w-full max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="sticky top-0 bg-card border-b border-border p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-foreground">
              {result ? '验证结果' : '关卡验证'}
            </h2>
            {!result && (
              <span className={`flex items-center gap-1 text-sm ${
                timeLeft < 60 ? 'text-red-500' : 'text-muted-foreground'
              }`}>
                <Clock className="w-4 h-4" />
                {formatTime(timeLeft)}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : result ? (
            <div className="text-center">
              {result.passed ? (
                <>
                  <div className="w-24 h-24 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="w-12 h-12 text-green-500" />
                  </div>
                  <h3 className="text-2xl font-bold text-foreground mb-2">
                    验证通过！
                  </h3>
                  <p className="text-muted-foreground mb-6">
                    恭喜你完成了本关卡的学习目标
                  </p>
                  <div className="flex justify-center gap-8 mb-8">
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-2 mb-1">
                        <Trophy className="w-5 h-5 text-yellow-500" />
                        <span className="text-2xl font-bold text-foreground">
                          +{result.xp_earned}
                        </span>
                      </div>
                      <span className="text-sm text-muted-foreground">经验值</span>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-2 mb-1">
                        <Zap className="w-5 h-5 text-blue-500" />
                        <span className="text-2xl font-bold text-foreground">
                          +{result.quota_bonus}
                        </span>
                      </div>
                      <span className="text-sm text-muted-foreground">AI配额</span>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="w-24 h-24 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <AlertCircle className="w-12 h-12 text-red-500" />
                  </div>
                  <h3 className="text-2xl font-bold text-foreground mb-2">
                    验证未通过
                  </h3>
                  <p className="text-muted-foreground mb-6">
                    答对 {result.correct_count}/{result.total_count} 题，需要答对60%以上才能通过
                  </p>
                  <p className="text-sm text-muted-foreground">
                    你可以重新尝试验证
                  </p>
                </>
              )}
            </div>
          ) : (
            <>
              {/* Questions */}
              <div className="space-y-6 mb-8">
                {questions.map((q, index) => (
                  <div key={q.id} className="bg-muted/50 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm font-medium text-muted-foreground">
                        第 {index + 1} 题
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        q.difficulty === 1 ? 'bg-green-500/10 text-green-500' :
                        q.difficulty === 2 ? 'bg-yellow-500/10 text-yellow-500' :
                        'bg-red-500/10 text-red-500'
                      }`}>
                        难度 {q.difficulty}
                      </span>
                    </div>
                    <p className="text-foreground mb-4">{q.content.text}</p>

                    {q.type === 'choice' && q.content.options && (
                      <div className="grid grid-cols-2 gap-2">
                        {q.content.options.map((opt, i) => (
                          <button
                            key={i}
                            onClick={() => setAnswers({ ...answers, [q.id]: opt })}
                            className={`p-3 rounded-lg border text-left text-sm transition-all ${
                              answers[q.id] === opt
                                ? 'border-primary bg-primary/10 text-primary'
                                : 'border-border hover:border-muted-foreground'
                            }`}
                          >
                            {opt}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Submit button */}
              <button
                onClick={handleSubmit}
                disabled={Object.keys(answers).length < questions.length || submitting}
                className="w-full py-4 bg-primary text-primary-foreground rounded-xl font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {submitting ? '提交中...' : '提交验证'}
              </button>
              <p className="text-center text-sm text-muted-foreground mt-3">
                已答 {Object.keys(answers).length}/{questions.length} 题
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
