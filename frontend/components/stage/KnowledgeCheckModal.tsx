'use client'

import { useState } from 'react'
import { X, CheckCircle, XCircle, Sparkles, BookOpen, ChevronRight } from 'lucide-react'

interface KnowledgeCheckQuestion {
  id: string
  question: string
  options: string[]
  correct_answer: string
  explanation?: string
  knowledge_point?: string
}

interface KnowledgeCheckModalProps {
  isOpen: boolean
  questions: KnowledgeCheckQuestion[]
  onComplete: (passed: boolean, correctCount: number) => void
  onClose: () => void
}

export function KnowledgeCheckModal({
  isOpen,
  questions,
  onComplete,
  onClose
}: KnowledgeCheckModalProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitted, setSubmitted] = useState(false)
  const [showResult, setShowResult] = useState(false)

  if (!isOpen || questions.length === 0) return null

  const question = questions[currentQuestion]
  const isLastQuestion = currentQuestion === questions.length - 1

  const handleAnswer = (option: string) => {
    if (submitted) return
    setAnswers({ ...answers, [question.id]: option })
  }

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    }
  }

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1)
    }
  }

  const handleSubmit = () => {
    setSubmitted(true)
    setShowResult(true)

    // 计算正确数量
    let correct = 0
    for (const q of questions) {
      if (answers[q.id] === q.correct_answer) {
        correct++
      }
    }

    const passed = correct >= Math.ceil(questions.length * 0.7)
    onComplete(passed, correct)
  }

  const getOptionStyle = (option: string) => {
    const isSelected = answers[question.id] === option
    const isCorrect = question.correct_answer === option

    if (!submitted) {
      return isSelected
        ? 'border-indigo-500 bg-indigo-500/20 text-white'
        : 'border-slate-600/50 hover:border-slate-500 hover:bg-slate-700/30 text-slate-300'
    }

    if (isCorrect) {
      return 'border-emerald-500 bg-emerald-500/20 text-emerald-300'
    }

    if (isSelected && !isCorrect) {
      return 'border-red-500 bg-red-500/20 text-red-300'
    }

    return 'border-slate-700 text-slate-500'
  }

  // Result view
  if (showResult) {
    const correctCount = questions.filter(q => answers[q.id] === q.correct_answer).length
    const passed = correctCount >= Math.ceil(questions.length * 0.7)

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700/50 shadow-2xl max-w-md w-full overflow-hidden">
          {/* Header */}
          <div className={`p-6 text-center ${passed ? 'bg-emerald-500/10' : 'bg-orange-500/10'}`}>
            <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 ${
              passed ? 'bg-emerald-500/20' : 'bg-orange-500/20'
            }`}>
              {passed ? (
                <CheckCircle className="w-10 h-10 text-emerald-400" />
              ) : (
                <XCircle className="w-10 h-10 text-orange-400" />
              )}
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              {passed ? '知识点掌握！' : '还需巩固'}
            </h2>
            <p className="text-slate-400">
              答对 <span className="font-bold text-white">{correctCount}</span> / {questions.length} 题
            </p>
          </div>

          {/* Questions review */}
          <div className="p-6 space-y-3">
            {questions.map((q, i) => {
              const isCorrect = answers[q.id] === q.correct_answer
              return (
                <div
                  key={q.id}
                  className={`p-3 rounded-xl border ${
                    isCorrect
                      ? 'border-emerald-500/30 bg-emerald-500/5'
                      : 'border-red-500/30 bg-red-500/5'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {isCorrect ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                    )}
                    <span className="text-sm text-slate-300 truncate">{q.question}</span>
                  </div>
                  {!isCorrect && q.explanation && (
                    <p className="mt-2 text-xs text-slate-400">{q.explanation}</p>
                  )}
                </div>
              )
            })}
          </div>

          {/* Actions */}
          <div className="p-6 pt-0">
            <button
              onClick={onClose}
              className={`w-full py-3 rounded-xl font-medium transition-colors ${
                passed
                  ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:from-emerald-600 hover:to-emerald-700'
                  : 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white hover:from-indigo-600 hover:to-indigo-700'
              }`}
            >
              {passed ? '继续学习' : '重新练习'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700/50 shadow-2xl max-w-2xl w-full overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-700/50 bg-gradient-to-r from-indigo-500/10 to-purple-500/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-500/20 rounded-xl flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">知识点验证</h2>
                <p className="text-sm text-slate-400">确认你理解了核心概念</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Progress */}
        <div className="px-4 pt-4">
          <div className="flex items-center gap-2">
            {questions.map((_, i) => (
              <div
                key={i}
                className={`flex-1 h-1.5 rounded-full transition-colors ${
                  i < currentQuestion
                    ? 'bg-emerald-500'
                    : i === currentQuestion
                    ? 'bg-indigo-500'
                    : 'bg-slate-700'
                }`}
              />
            ))}
          </div>
          <p className="text-sm text-slate-400 mt-2">
            问题 {currentQuestion + 1} / {questions.length}
          </p>
        </div>

        {/* Question */}
        <div className="p-6">
          <div className="mb-2">
            {question.knowledge_point && (
              <span className="text-xs font-medium text-indigo-400 bg-indigo-500/10 px-2 py-1 rounded-full">
                {question.knowledge_point}
              </span>
            )}
          </div>
          <h3 className="text-xl font-semibold text-white mb-6">
            {question.question}
          </h3>

          <div className="space-y-3">
            {question.options.map((option, i) => (
              <button
                key={i}
                onClick={() => handleAnswer(option)}
                className={`w-full p-4 rounded-xl border-2 text-left transition-all ${getOptionStyle(option)}`}
              >
                <div className="flex items-center gap-3">
                  <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium ${
                    answers[question.id] === option
                      ? 'bg-indigo-500 text-white'
                      : 'bg-slate-700 text-slate-300'
                  }`}>
                    {String.fromCharCode(65 + i)}
                  </span>
                  <span>{option}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="p-6 pt-0 flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            className="px-4 py-2 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            上一题
          </button>

          <div className="flex gap-3">
            {!isLastQuestion ? (
              <button
                onClick={handleNext}
                disabled={!answers[question.id]}
                className="px-6 py-2.5 bg-indigo-500 text-white rounded-xl font-medium hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                下一题
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={Object.keys(answers).length < questions.length}
                className="px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-xl font-medium hover:from-emerald-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                提交验证
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
