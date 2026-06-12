'use client'

import { useEffect, useRef, useState } from 'react'
import { Sparkles, Gem, Loader2, AlertCircle } from 'lucide-react'
import { HINT_CONFIG, type HintLevel, HintMessage } from './HintMessage'
import { CloseButton, CostLabel, ErrorToast } from './HintActions'

// ========================================
// Legacy non-streaming AIHintButton / AIHintPanel
// Preserved for parity with the pre-split file. Verified unused by
// `npx codegraph impact` (no external references). See AGENTS.md Rule 7.
// ========================================

interface LegacyAIHintButtonProps {
  level: HintLevel
  onGetHint: (level: HintLevel) => Promise<{ hint: string; cost: number } | null>
  disabled?: boolean
  currentBalance?: number
}

function AIHintButton({ level, onGetHint, disabled, currentBalance }: LegacyAIHintButtonProps) {
  const [loading, setLoading] = useState(false)
  const [hint, setHint] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (hint) {
      if (!dialog.open) dialog.showModal()
    } else {
      if (dialog.open) dialog.close()
    }
  }, [hint])

  const config = HINT_CONFIG[level]
  const Icon = config.icon
  const canAfford = currentBalance === undefined || currentBalance >= config.cost

  const fetchHint = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await onGetHint(level)
      if (result) setHint(result.hint)
    } catch {
      setError('获取提示失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setHint(null)
    setError(null)
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={fetchHint}
        disabled={disabled || loading || !canAfford}
        className={`
          flex flex-col items-center gap-1 p-2 rounded-lg border transition-all
          ${config.bgColor} ${config.borderColor} ${config.hoverColor}
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
        title={`${config.label}: ${config.description} (-${config.cost}智核)`}
      >
        {loading ? (
          <Loader2 className={`size-5 ${config.color} animate-spin`} />
        ) : (
          <Icon className={`size-5 ${config.color}`} />
        )}
        <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
        <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
          <Gem className="size-3" />
          {config.cost}
        </span>
      </button>

      {!canAfford && (
        <div className="absolute -top-1 -right-1 size-3 bg-red-500 rounded-full flex items-center justify-center">
          <AlertCircle className="size-2 text-white" />
        </div>
      )}

      <dialog
        ref={dialogRef}
        className="fixed inset-0 z-50 m-0 h-screen w-screen max-w-none max-h-none bg-transparent p-0 open:flex open:items-center open:justify-center backdrop:bg-black/40 backdrop:backdrop-blur-xl"
        onClose={handleClose}
        aria-modal="true"
      >
        <div
          className="relative w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col rounded-2xl border border-white/10 shadow-2xl bg-card/95 backdrop-blur-sm animate-modal-enter m-4"
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
        >
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

          <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-border/50 bg-gradient-to-r from-primary/5 via-primary/[0.02] to-transparent">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${config.bgColor}`}>
                <Icon className={`size-5 ${config.color}`} />
              </div>
              <h3 className="text-lg font-semibold text-foreground">{config.label}</h3>
            </div>
            <CloseButton onClick={handleClose} ariaLabel="关闭" />
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-4">
            <HintMessage content={hint ?? ''} />
          </div>

          <div className="px-6 py-4 border-t border-border/50 bg-muted/30 flex items-center justify-between">
            <CostLabel level={level} />
            <button
              type="button"
              onClick={handleClose}
              className="px-5 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-primary to-primary-600 text-primary-foreground hover:from-primary-600 hover:to-primary-700 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5"
            >
              知道了
            </button>
          </div>
        </div>
      </dialog>

      {error && <ErrorToast message={error} onDismiss={() => setError(null)} />}
    </div>
  )
}

interface LegacyAIHintPanelProps {
  onGetHint: (level: HintLevel) => Promise<{ hint: string; cost: number } | null>
  currentBalance?: number
  disabled?: boolean
}

export function LegacyAIHintPanel({ onGetHint, currentBalance, disabled }: LegacyAIHintPanelProps) {
  return (
    <div className="bg-card rounded-xl border p-4">
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
      <div className="flex gap-2">
        <AIHintButton level="light" onGetHint={onGetHint} disabled={disabled} currentBalance={currentBalance} />
        <AIHintButton level="medium" onGetHint={onGetHint} disabled={disabled} currentBalance={currentBalance} />
        <AIHintButton level="deep" onGetHint={onGetHint} disabled={disabled} currentBalance={currentBalance} />
      </div>
    </div>
  )
}
