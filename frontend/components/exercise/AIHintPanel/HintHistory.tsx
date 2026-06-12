'use client'

import { Sparkles, Gem } from 'lucide-react'

interface HintHistoryProps {
  currentBalance?: number
}

/**
 * HintHistory - the panel header showing the AI hint title + current balance.
 * Mirrors the original `StreamHintPanel` header layout.
 */
export function HintHistory({ currentBalance }: HintHistoryProps) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
        <Sparkles className="size-4 text-purple-500" />
        AI 提示
      </h3>
      {currentBalance !== undefined && (
        <span className="text-xs text-muted-foreground flex items-center gap-1">
          <Gem className="size-3 text-purple-500" />
          {currentBalance}
        </span>
      )}
    </div>
  )
}
