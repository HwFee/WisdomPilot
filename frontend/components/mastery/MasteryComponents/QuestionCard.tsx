'use client'

import { MasteryProgressBar } from './ProgressBar'

// ========================================
// KnowledgePointMasteryCard - single knowledge point "question" card
// Shows: name, attempts, accuracy, mastery badge, progress bar.
// ========================================

interface KnowledgePointMasteryProps {
  name: string
  pL: number // 0-1 的掌握概率
  totalAttempts: number
  correctAttempts: number
  isMastered: boolean
}

export function KnowledgePointMasteryCard({
  name,
  pL,
  totalAttempts,
  correctAttempts,
  isMastered,
}: KnowledgePointMasteryProps) {
  const score = pL * 100
  const accuracy = totalAttempts > 0 ? (correctAttempts / totalAttempts) * 100 : 0

  return (
    <div className="bg-white rounded-lg border border-gray-100 p-3 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-gray-900 truncate">{name}</h4>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            <span>尝试 {totalAttempts} 次</span>
            <span>•</span>
            <span>正确率 {accuracy.toFixed(0)}%</span>
          </div>
        </div>
        <div className="flex-shrink-0 ml-2">
          {isMastered ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
              ✓ 已掌握
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
              学习中
            </span>
          )}
        </div>
      </div>
      <div className="mt-2">
        <MasteryProgressBar score={score} size="sm" showLabel={false} />
      </div>
    </div>
  )
}
