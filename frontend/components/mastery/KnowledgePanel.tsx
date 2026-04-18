/**
 * Knowledge Panel Component
 *
 * Displays chapter knowledge content for mastery path learning.
 * Shows AI-generated knowledge points with code examples.
 */

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { KnowledgeContentResponse, KnowledgePoint } from '@/types/api'

interface KnowledgePanelProps {
  content: KnowledgeContentResponse | null
  isLoading?: boolean
  onStartQuiz: () => void
  onClose: () => void
}

export function KnowledgePanel({
  content,
  isLoading = false,
  onStartQuiz,
  onClose,
}: KnowledgePanelProps) {
  const [expandedPoint, setExpandedPoint] = useState<string | null>(
    content?.knowledge_points[0]?.id || null
  )

  const togglePoint = (pointId: string) => {
    setExpandedPoint(prev => (prev === pointId ? null : pointId))
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 shadow-2xl max-w-2xl w-full mx-4">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/2" />
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-4 bg-gray-200 rounded w-2/3" />
            <div className="h-32 bg-gray-200 rounded" />
          </div>
          <p className="text-center text-gray-500 mt-4">加载中...</p>
        </div>
      </div>
    )
  }

  if (!content) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 shadow-2xl max-w-2xl w-full mx-4">
          <p className="text-center text-gray-500">无法加载知识点内容</p>
          <button
            onClick={onClose}
            className="mt-4 w-full py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            关闭
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{content.chapter_title}</h2>
              <p className="text-sm text-gray-500 mt-1">知识点讲解</p>
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

          {/* Stats */}
          <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              {content.total_points} 个知识点
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              预计学习时间 {content.estimated_time} 分钟
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {content.knowledge_points.map((point, index) => {
              const prevPoint = index > 0 ? content.knowledge_points[index - 1] : undefined
              const nextPoint = index < content.knowledge_points.length - 1 ? content.knowledge_points[index + 1] : undefined
              const adjacent = [prevPoint, nextPoint].filter(Boolean) as KnowledgePoint[]
              return (
                <KnowledgePointCard
                  key={point.id}
                  point={point}
                  index={index}
                  isExpanded={expandedPoint === point.id}
                  onToggle={() => togglePoint(point.id)}
                  adjacentPoints={adjacent}
                />
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-100 flex-shrink-0">
          <button
            onClick={onStartQuiz}
            className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            开始测试
          </button>
        </div>
      </motion.div>
    </div>
  )
}

interface KnowledgePointCardProps {
  point: KnowledgePoint
  index: number
  isExpanded: boolean
  onToggle: () => void
  adjacentPoints?: KnowledgePoint[]
}

function KnowledgePointCard({ point, index, isExpanded, onToggle, adjacentPoints }: KnowledgePointCardProps & { adjacentPoints?: KnowledgePoint[] }) {
  const examplesJson = point.examples && point.examples.length > 0
    ? JSON.stringify(point.examples)
    : '[]'
  const adjacentJson = adjacentPoints && adjacentPoints.length > 0
    ? JSON.stringify(adjacentPoints.map(p => ({ id: p.id, title: p.title })))
    : '[]'

  return (
    <motion.div
      layout
      className="border border-gray-100 rounded-xl overflow-hidden hover:border-blue-200 transition-colors"
      data-knowledge-point
      data-knowledge-point-id={point.id}
      data-knowledge-point-title={point.title}
      data-knowledge-point-content={point.content}
      data-knowledge-point-examples={examplesJson}
      data-knowledge-point-difficulty={point.difficulty}
      data-knowledge-point-index={index}
      data-knowledge-point-adjacent={adjacentJson}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full p-4 text-left flex items-start gap-3 hover:bg-gray-50 transition-colors"
      >
        <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">{point.title}</h3>
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <DifficultyBadge difficulty={point.difficulty} />
          </div>
        </div>
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3">
              {/* Content */}
              <p className="text-gray-600 leading-relaxed">{point.content}</p>

              {/* Code Examples */}
              {point.examples && point.examples.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">示例代码</p>
                  <div className="space-y-1">
                    {point.examples.map((example, i) => (
                      <div
                        key={i}
                        className="bg-gray-900 text-gray-100 rounded-lg p-3 font-mono text-sm overflow-x-auto"
                      >
                        {example}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Related Points */}
              {point.related_points && point.related_points.length > 0 && (
                <div className="text-sm text-gray-500">
                  <span className="font-medium">相关知识点：</span>
                  {point.related_points.join('、')}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
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
