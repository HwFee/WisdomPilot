'use client'

import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github-dark.css'

import { HintHistory } from './HintHistory'
import { HintBubble, type ExerciseHintData } from './HintBubble'
import { LegacyAIHintPanel } from './LegacyAIHint'

export type { ExerciseHintData } from './HintBubble'
export { LegacyAIHintPanel }

// ========================================
// StreamHintPanel - top-level AI hint panel
// 3 hint bubbles (light/medium/deep), each opens a draggable streaming modal.
// This is the entry point imported by arena-problem-panel.
// ========================================

interface StreamHintPanelProps {
  exerciseData: ExerciseHintData
  token: string
  onBalanceChange: () => void
  currentBalance?: number
  disabled?: boolean
}

export function StreamHintPanel({
  exerciseData,
  token,
  onBalanceChange,
  currentBalance,
  disabled,
}: StreamHintPanelProps) {
  return (
    <div className="bg-card rounded-xl border p-4">
      <HintHistory currentBalance={currentBalance} />
      <div className="flex gap-2">
        <HintBubble
          level="light"
          exerciseData={exerciseData}
          token={token}
          onBalanceChange={onBalanceChange}
          disabled={disabled}
          currentBalance={currentBalance}
        />
        <HintBubble
          level="medium"
          exerciseData={exerciseData}
          token={token}
          onBalanceChange={onBalanceChange}
          disabled={disabled}
          currentBalance={currentBalance}
        />
        <HintBubble
          level="deep"
          exerciseData={exerciseData}
          token={token}
          onBalanceChange={onBalanceChange}
          disabled={disabled}
          currentBalance={currentBalance}
        />
      </div>
    </div>
  )
}
