'use client'

import { CheckCircle, XCircle, ArrowRight, RotateCcw } from 'lucide-react'

type FeedbackState = 'idle' | 'correct' | 'wrong'

interface FeedbackPanelProps {
  state: FeedbackState
  message?: string
  correctAnswer?: string
  xpEarned?: number
  onNext?: () => void
  onRetry?: () => void
  lang?: 'zh' | 'en'
}

export function FeedbackPanel({
  state,
  message,
  correctAnswer,
  xpEarned = 0,
  onNext,
  onRetry,
  lang = 'zh',
}: FeedbackPanelProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  if (state === 'idle') {
    return (
      <div className="bg-card border-t border-border p-4">
        <button
          className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={state !== 'idle'}
        >
          {t('提交运行', 'Submit')}
        </button>
      </div>
    )
  }

  if (state === 'correct') {
    return (
      <div className="bg-gradient-to-r from-emerald-500/20 to-emerald-500/10 border-t border-emerald-500/30 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-emerald-500" />
            </div>
            <div>
              <p className="font-semibold text-emerald-600">{t('太棒了！', 'Great job!')}</p>
              {xpEarned > 0 && (
                <p className="text-sm text-emerald-600/80">+{xpEarned} XP</p>
              )}
            </div>
          </div>
          {onNext && (
            <button
              onClick={onNext}
              className="flex items-center gap-2 px-6 py-3 bg-emerald-500 text-white rounded-xl font-medium hover:bg-emerald-600 transition-colors"
            >
              {t('下一题', 'Next')}
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
        {message && (
          <p className="mt-3 text-sm text-emerald-600/80">{message}</p>
        )}
      </div>
    )
  }

  if (state === 'wrong') {
    return (
      <div className="bg-gradient-to-r from-red-500/20 to-red-500/10 border-t border-red-500/30 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
              <XCircle className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <p className="font-semibold text-red-600">{t('答案错误', 'Incorrect')}</p>
              {message && (
                <p className="text-sm text-red-600/80">{message}</p>
              )}
            </div>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center gap-2 px-6 py-3 bg-red-500 text-white rounded-xl font-medium hover:bg-red-600 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              {t('重试', 'Retry')}
            </button>
          )}
        </div>
        {correctAnswer && (
          <div className="mt-3 p-3 bg-red-500/10 rounded-lg">
            <p className="text-xs text-muted-foreground mb-1">{t('正确答案', 'Correct Answer')}</p>
            <pre className="text-sm font-mono text-red-600">{correctAnswer}</pre>
          </div>
        )}
      </div>
    )
  }

  return null
}
