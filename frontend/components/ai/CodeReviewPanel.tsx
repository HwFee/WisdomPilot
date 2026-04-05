'use client'

import { useState } from 'react'
import { getStoredToken } from '@/lib/api'
import { getCodeReview, CodeReviewRequest } from '@/lib/ai-api'
import { Bot, Loader2, X, AlertCircle, Star } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CodeReviewPanelProps {
  code: string
  language: string
  chapterId?: number
  subsectionIndex?: number
  onClose?: () => void
  className?: string
}

export function CodeReviewPanel({
  code,
  language,
  chapterId,
  subsectionIndex,
  onClose,
  className,
}: CodeReviewPanelProps) {
  const [review, setReview] = useState<string | null>(null)
  const [score, setScore] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleReview = async () => {
    const token = getStoredToken()
    if (!token) return

    setIsLoading(true)
    setError(null)

    try {
      const request: CodeReviewRequest = {
        code,
        language,
        chapter_id: chapterId,
        subsection_index: subsectionIndex,
      }

      const response = await getCodeReview(token, request)
      setReview(response.review)
      setScore(response.score ?? null)
    } catch (err) {
      setError(err instanceof Error ? err.message : '代码审查失败')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={cn('flex flex-col h-full bg-gray-900', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-violet-400" />
          <span className="text-sm font-medium text-gray-200">AI 代码审查</span>
          {score !== null && (
            <div className="flex items-center gap-1 ml-2">
              <Star className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-xs text-yellow-400">{score}/100</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleReview}
            disabled={isLoading || !code.trim()}
            className="flex items-center gap-1.5 px-3 py-1 bg-violet-600 text-white text-xs rounded hover:bg-violet-700 disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Bot className="w-3 h-3" />
            )}
            {isLoading ? '分析中...' : '开始审查'}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4">
        {isLoading && (
          <div className="flex items-center gap-3 text-gray-400">
            <Loader2 className="w-5 h-5 animate-spin text-violet-400" />
            <span className="text-sm">AI 正在审查代码...</span>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2 text-red-400">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {review && (
          <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
            {review}
          </pre>
        )}

        {!review && !isLoading && !error && (
          <div className="text-center text-gray-500 py-8">
            <Bot className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">点击&quot;开始审查&quot;让 AI 分析你的代码</p>
            <p className="text-xs mt-1 text-gray-600">
              AI 将检查代码质量、潜在问题和优化建议
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
