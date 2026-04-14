'use client'

import { X, Zap } from 'lucide-react'

interface ExerciseHeaderProps {
  stageName: string
  currentQuestion: number
  totalQuestions: number
  xpEarned: number
  timeLimit?: number // in seconds
  onExit: () => void
  lang?: 'zh' | 'en'
}

export function ExerciseHeader({
  stageName,
  currentQuestion,
  totalQuestions,
  xpEarned,
  timeLimit,
  onExit,
  lang = 'zh',
}: ExerciseHeaderProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-14 bg-card/95 backdrop-blur-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-4 h-full flex items-center justify-between">
        {/* Left: Exit */}
        <button
          onClick={onExit}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="w-5 h-5" />
          <span className="text-sm">{t('退出', 'Exit')}</span>
        </button>

        {/* Center: Stage name + progress */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-foreground">{stageName}</span>
          <div className="flex items-center gap-1">
            {[...Array(totalQuestions)].map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full ${
                  i < currentQuestion
                    ? 'bg-primary'
                    : i === currentQuestion
                    ? 'bg-primary/50'
                    : 'bg-muted'
                }`}
              />
            ))}
          </div>
          <span className="text-sm text-muted-foreground">
            {currentQuestion + 1}/{totalQuestions}
          </span>
        </div>

        {/* Right: XP + Time */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-yellow-500/10 rounded-full">
            <Zap className="w-4 h-4 text-yellow-500" />
            <span className="text-sm font-medium text-yellow-600">{xpEarned} XP</span>
          </div>
          {timeLimit !== undefined && (
            <div className="text-sm text-muted-foreground font-mono">
              {formatTime(timeLimit)}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
