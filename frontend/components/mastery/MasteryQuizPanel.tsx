/**
 * Mastery Quiz Panel Component
 *
 * Displays quiz questions for mastery path learning.
 * Supports choice and programming questions.
 */

'use client'

import { useState } from 'react'
import { LazyMotion, domAnimation, m, AnimatePresence } from 'framer-motion'
import type { MasteryQuizQuestion, QuizAnswer } from '@/types/api'

interface MasteryQuizPanelProps {
  questions: MasteryQuizQuestion[]
  onSubmit: (answers: QuizAnswer[], totalTime: number) => void
  onClose: () => void
  onOpenEditor?: (template: string, question: string) => void
}

export function MasteryQuizPanel({
  questions,
  onSubmit,
  onClose,
  onOpenEditor,
}: MasteryQuizPanelProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Map<string, string>>(() => new Map())
  const [startTime] = useState(() => Date.now())

  const currentQuestion = questions[currentIndex]
  const isLastQuestion = currentIndex === questions.length - 1
  const progress = ((currentIndex + 1) / questions.length) * 100
  const selectedOption = currentQuestion ? answers.get(currentQuestion.id) || null : null

  const handleSelectOption = (option: string) => {
    if (!currentQuestion) return
    setAnswers(prev => {
      const next = new Map(prev)
      next.set(currentQuestion.id, option)
      return next
    })
  }

  const handleNext = () => {
    if (isLastQuestion) {
      // Submit all answers
      const finalAnswers: QuizAnswer[] = questions.map(q => ({
        question_id: q.id,
        answer: answers.get(q.id) || '',
      }))
      const totalTime = Math.floor((Date.now() - startTime) / 1000)
      onSubmit(finalAnswers, totalTime)
    } else {
      setCurrentIndex(prev => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1)
    }
  }

  if (!currentQuestion) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xl">
      <LazyMotion features={domAnimation}>
        <m.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 12 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col rounded-2xl border border-white/10 shadow-2xl bg-card/95 backdrop-blur-sm"
        >
        {/* 顶部光效 */}
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

        {/* Header */}
        <div className="p-6 border-b border-border/50 flex-shrink-0 bg-gradient-to-r from-primary/5 via-primary/[0.02] to-transparent">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-foreground">精进之路测试</h2>
              <p className="text-sm text-muted-foreground mt-1">
                第 {currentIndex + 1} / {questions.length} 题
              </p>
            </div>
            <button type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg bg-muted/50 hover:bg-muted border border-border/50 hover:border-border transition-all group"
              aria-label="关闭"
            >
              <svg className="size-4 text-muted-foreground group-hover:text-foreground transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Progress bar */}
          <div className="mt-4 h-2 bg-muted rounded-full overflow-hidden">
            <m.div
              className="h-full bg-gradient-to-r from-primary to-primary-600"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>

        {/* Question Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <m.div
              key={currentQuestion.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Difficulty Badge */}
              <div className="flex items-center gap-2 mb-4">
                <DifficultyBadge difficulty={currentQuestion.difficulty} />
                <span className="text-xs text-muted-foreground">
                  {currentQuestion.knowledge_points.join('、')}
                </span>
              </div>

              {/* Question Text */}
              <p className="text-lg text-foreground mb-6">
                {currentQuestion.content.text}
              </p>

              {/* Options for Choice Questions */}
              {currentQuestion.type === 'choice' && currentQuestion.content.options && (
                <div className="flex flex-col gap-y-3">
                  {currentQuestion.content.options.map((option, index) => {
                    const optionLabel = String.fromCharCode(65 + index) // A, B, C, D
                    const isSelected = selectedOption === optionLabel

                    return (
                      <button type="button"
                        key={`option-${optionLabel}`}
                        onClick={() => handleSelectOption(optionLabel)}
                        className={`w-full p-4 text-left rounded-xl border-2 transition-all ${
                          isSelected
                            ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                            : 'border-border/50 hover:border-border hover:bg-muted/50'
                        }`}
                      >
                        <span className="font-medium text-foreground">
                          {optionLabel}. {option}
                        </span>
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Programming Question */}
              {currentQuestion.type === 'programming' && (
                <div className="flex flex-col gap-y-4">
                  <div className="bg-muted rounded-xl p-4 overflow-x-auto border border-border/50">
                    <pre className="text-foreground text-sm font-mono whitespace-pre-wrap">
                      {currentQuestion.content.code_template || '// 请在此编写代码'}
                    </pre>
                  </div>

                  {currentQuestion.content.test_cases && currentQuestion.content.test_cases.length > 0 && (
                    <div className="flex flex-col gap-y-2">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">测试用例</p>
                      <div className="bg-muted/50 rounded-lg p-3 text-sm font-mono flex flex-col gap-y-1 border border-border/50">
                        {currentQuestion.content.test_cases.map((tc) => (
                          <div key={`tc-${tc.input}-${tc.expected}`} className="flex gap-2">
                            <span className="text-muted-foreground">输入:</span>
                            <span className="text-foreground">{tc.input}</span>
                            <span className="text-muted-foreground ml-2">期望:</span>
                            <span className="text-green-600">{tc.expected}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-center">
                    <button type="button"
                      onClick={() => {
                        if (onOpenEditor) {
                          onOpenEditor(
                            currentQuestion.content.code_template || '',
                            currentQuestion.content.text
                          )
                        }
                      }}
                      className="px-6 py-3 bg-gradient-to-r from-primary to-primary-600 text-primary-foreground rounded-xl font-medium hover:from-primary-600 hover:to-primary-700 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5 flex items-center gap-2"
                    >
                      <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                      </svg>
                      打开编辑器
                    </button>
                  </div>
                </div>
              )}
            </m.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border/50 flex-shrink-0 bg-muted/30">
          <div className="flex items-center justify-between gap-4">
            <button type="button"
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className={`px-4 py-2 rounded-lg transition-colors ${
                currentIndex === 0
                  ? 'text-muted-foreground/30 cursor-not-allowed'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
            >
              上一题
            </button>

            <button type="button"
              onClick={handleNext}
              disabled={!selectedOption}
              className={`flex-1 py-3 rounded-xl font-medium transition-all ${
                !selectedOption
                  ? 'bg-muted text-muted-foreground/50 cursor-not-allowed'
                  : 'bg-gradient-to-r from-primary to-primary-600 text-primary-foreground hover:from-primary-600 hover:to-primary-700 shadow-sm hover:shadow-md hover:-translate-y-0.5'
              }`}
            >
              {isLastQuestion ? '提交' : '下一题'}
            </button>
          </div>
        </div>
      </m.div>
    </LazyMotion>
  </div>
  )
}

const DIFFICULTY_COLORS = {
  1: 'bg-green-100 text-green-700',
  2: 'bg-blue-100 text-blue-700',
  3: 'bg-yellow-100 text-yellow-700',
  4: 'bg-orange-100 text-orange-700',
  5: 'bg-red-100 text-red-700',
}

const DIFFICULTY_LABELS = {
  1: '入门',
  2: '基础',
  3: '中等',
  4: '较难',
  5: '困难',
}

function DifficultyBadge({ difficulty }: { difficulty: number }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${DIFFICULTY_COLORS[difficulty as keyof typeof DIFFICULTY_COLORS] || DIFFICULTY_COLORS[1]}`}>
      {DIFFICULTY_LABELS[difficulty as keyof typeof DIFFICULTY_LABELS] || '入门'}
    </span>
  )
}
