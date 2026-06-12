'use client'

import { X, AlertCircle } from 'lucide-react'
import { Gem } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { HintLevel } from './HintMessage'
import { HINT_CONFIG } from './HintMessage'

// ========================================
// Modal close button (header X)
// ========================================

interface CloseButtonProps {
  onClick: () => void
  ariaLabel?: string
}

export function CloseButton({ onClick, ariaLabel = '关闭' }: CloseButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="p-1.5 rounded-lg bg-muted/50 hover:bg-muted border border-border/50 hover:border-border transition-all group"
      aria-label={ariaLabel}
    >
      <X className="size-4 text-muted-foreground group-hover:text-foreground transition-colors" />
    </button>
  )
}

// ========================================
// Modal footer action (知道了 / 关闭)
// ========================================

interface ModalFooterActionProps {
  isStreaming: boolean
  isCached: boolean
  onClose: () => void
}

export function ModalFooterAction({ isStreaming, isCached, onClose }: ModalFooterActionProps) {
  const label = isStreaming && !isCached ? '关闭' : '知道了'
  return (
    <button
      type="button"
      onClick={onClose}
      className="px-5 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-primary to-primary-600 text-primary-foreground hover:from-primary-600 hover:to-primary-700 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5"
    >
      {label}
    </button>
  )
}

// ========================================
// Cost label (left side of modal footer)
// ========================================

interface CostLabelProps {
  level: HintLevel
  isCached?: boolean
  lang?: 'zh' | 'en'
}

export function CostLabel({ level, isCached, lang = 'zh' }: CostLabelProps) {
  const cost = HINT_CONFIG[level].cost
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  if (isCached) {
    return (
      <span className="text-sm text-muted-foreground">
        <span className="text-green-600">{t('免费查看（已购买）', 'Free (already purchased)')}</span>
      </span>
    )
  }

  return (
    <span className="text-sm text-muted-foreground flex items-center gap-1">
      {t('消耗', 'Cost')} <Gem className="size-4 text-purple-500" /> {cost} {t('智核', 'credits')}
    </span>
  )
}

// ========================================
// Error toast (fixed bottom-right)
// ========================================

interface ErrorToastProps {
  message: string
  onDismiss: () => void
  className?: string
}

export function ErrorToast({ message, onDismiss, className }: ErrorToastProps) {
  return (
    <div
      className={cn(
        'fixed bottom-4 right-4 z-50 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2',
        className
      )}
    >
      <AlertCircle className="size-4" />
      {message}
      <button type="button" onClick={onDismiss} className="ml-2" aria-label="关闭错误提示">
        <X className="size-4" />
      </button>
    </div>
  )
}
