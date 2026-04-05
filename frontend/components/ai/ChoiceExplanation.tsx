'use client'

import { useState } from 'react'
import { getStoredToken } from '@/lib/api'
import { getChoiceExplanation, ChoiceExplanationRequest } from '@/lib/ai-api'
import { Bot, Loader2, X, AlertCircle } from 'lucide-react'

interface ChoiceExplanationProps {
  chapterId: number
  subsectionIndex: number
  exerciseId: number
  question: string
  options: string[]
  userSelectedIndex: number
  correctIndex: number
}

export function ChoiceExplanation({
  chapterId,
  subsectionIndex,
  exerciseId,
  question,
  options,
  userSelectedIndex,
  correctIndex,
}: ChoiceExplanationProps) {
  const [explanation, setExplanation] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  const handleGetExplanation = async () => {
    const token = getStoredToken()
    if (!token) return

    setIsLoading(true)
    setError(null)
    setIsOpen(true)

    try {
      const request: ChoiceExplanationRequest = {
        chapter_id: chapterId,
        subsection_index: subsectionIndex,
        exercise_id: exerciseId,
        question,
        options,
        user_selected_index: userSelectedIndex,
        correct_index: correctIndex,
      }

      const response = await getChoiceExplanation(token, request)
      setExplanation(response.explanation)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取 AI 解答失败')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setIsOpen(false)
    setExplanation(null)
    setError(null)
  }

  if (!isOpen) {
    return (
      <button
        onClick={handleGetExplanation}
        disabled={isLoading}
        className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-violet-600 to-indigo-600 text-white text-xs rounded-lg hover:from-violet-700 hover:to-indigo-700 transition-all disabled:opacity-50"
      >
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Bot className="w-3.5 h-3.5" />
        )}
        {isLoading ? 'AI 分析中...' : 'AI 解答'}
      </button>
    )
  }

  return (
    <div className="mt-3 border border-violet-200 rounded-lg bg-gradient-to-br from-violet-50 to-indigo-50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4" />
          <span className="text-sm font-medium">AI 智能分析</span>
        </div>
        <button
          onClick={handleClose}
          className="p-1 hover:bg-white/20 rounded transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {isLoading && (
          <div className="flex items-center gap-3 text-gray-600">
            <Loader2 className="w-5 h-5 animate-spin text-violet-600" />
            <span className="text-sm">AI 正在分析你的答案...</span>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2 text-red-600">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {explanation && (
          <div className="space-y-3">
            {/* 错误分析 */}
            <div className="bg-white rounded-lg p-3 border border-violet-100">
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {explanation}
              </p>
            </div>

            {/* 选项对比 */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-red-50 border border-red-200 rounded p-2">
                <span className="text-red-600 font-medium">你的选择：</span>
                <span className="text-gray-700">
                  {String.fromCharCode(65 + userSelectedIndex)}. {options[userSelectedIndex]}
                </span>
              </div>
              <div className="bg-green-50 border border-green-200 rounded p-2">
                <span className="text-green-600 font-medium">正确答案：</span>
                <span className="text-gray-700">
                  {String.fromCharCode(65 + correctIndex)}. {options[correctIndex]}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
