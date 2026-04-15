/**
 * Mastery Quiz Panel Component
 *
 * Displays quiz questions for mastery path learning.
 * Supports choice and programming questions.
 */

'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
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
  const [answers, setAnswers] = useState<Map<string, string>>(new Map())
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [startTime] = useState(Date.now())

  const currentQuestion = questions[currentIndex]
  const isLastQuestion = currentIndex === questions.length - 1
  const progress = ((currentIndex + 1) / questions.length) * 100

  // Reset selected option when question changes
  useEffect(() => {
    const savedAnswer = answers.get(currentQuestion?.id)
    setSelectedOption(savedAnswer || null)
  }, [currentIndex, currentQuestion?.id, answers])

  const handleSelectOption = (option: string) => {
    setSelectedOption(option)
    setAnswers(prev => {
      const newMap = new Map(prev)
      newMap.set(currentQuestion.id, option)
      return newMap
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">精进之路测试</h2>
              <p className="text-sm text-gray-500 mt-1">
                第 {currentIndex + 1} / {questions.length} 题
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="关闭"
            >
              <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Progress bar */}
          <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-blue-500"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>

        {/* Question Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentQuestion.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Difficulty Badge */}
              <div className="flex items-center gap-2 mb-4">
                <DifficultyBadge difficulty={currentQuestion.difficulty} />
                <span className="text-xs text-gray-500">
                  {currentQuestion.knowledge_points.join('、')}
                </span>
              </div>

              {/* Question Text */}
              <p className="text-lg text-gray-900 mb-6">
                {currentQuestion.content.text}
              </p>

              {/* Options for Choice Questions */}
              {currentQuestion.type === 'choice' && currentQuestion.content.options && (
                <div className="space-y-3">
                  {currentQuestion.content.options.map((option, index) => {
                    const optionLabel = String.fromCharCode(65 + index) // A, B, C, D
                    const isSelected = selectedOption === optionLabel

                    return (
                      <button
                        key={index}
                        onClick={() => handleSelectOption(optionLabel)}
                        className={`w-full p-4 text-left rounded-xl border-2 transition-all ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-500'
                            : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <span className="font-medium text-gray-900">
                          {optionLabel}. {option}
                        </span>
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Programming Question */}
              {currentQuestion.type === 'programming' && (
                <div className="space-y-4">
                  <div className="bg-gray-900 rounded-xl p-4 overflow-x-auto">
                    <pre className="text-gray-100 text-sm font-mono whitespace-pre-wrap">
                      {currentQuestion.content.code_template || '// 请在此编写代码'}
                    </pre>
                  </div>

                  {currentQuestion.content.test_cases && currentQuestion.content.test_cases.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">测试用例</p>
                      <div className="bg-gray-50 rounded-lg p-3 text-sm font-mono space-y-1">
                        {currentQuestion.content.test_cases.map((tc, idx) => (
                          <div key={idx} className="flex gap-2">
                            <span className="text-gray-500">输入:</span>
                            <span>{tc.input}</span>
                            <span className="text-gray-500 ml-2">期望:</span>
                            <span className="text-green-600">{tc.expected}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-center">
                    <button
                      onClick={() => {
                        if (onOpenEditor) {
                          onOpenEditor(
                            currentQuestion.content.code_template || '',
                            currentQuestion.content.text
                          )
                        }
                      }}
                      className="px-6 py-3 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                      </svg>
                      打开编辑器
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-100 flex-shrink-0">
          <div className="flex items-center justify-between gap-4">
            <button
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className={`px-4 py-2 rounded-lg transition-colors ${
                currentIndex === 0
                  ? 'text-gray-300 cursor-not-allowed'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              上一题
            </button>

            <button
              onClick={handleNext}
              disabled={!selectedOption}
              className={`flex-1 py-3 rounded-xl font-medium transition-colors ${
                !selectedOption
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isLastQuestion ? '提交' : '下一题'}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

function DifficultyBadge({ difficulty }: { difficulty: number }) {
  const colors = {
    1: 'bg-green-100 text-green-700',
    2: 'bg-blue-100 text-blue-700',
    3: 'bg-yellow-100 text-yellow-700',
    4: 'bg-orange-100 text-orange-700',
    5: 'bg-red-100 text-red-700',
  }

  const labels = {
    1: '入门',
    2: '基础',
    3: '中等',
    4: '较难',
    5: '困难',
  }

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[difficulty as keyof typeof colors] || colors[1]}`}>
      {labels[difficulty as keyof typeof labels] || '入门'}
    </span>
  )
}
