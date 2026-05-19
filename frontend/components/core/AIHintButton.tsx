'use client'

import { useState, useTransition } from 'react'
import { Gem, Lightbulb, Sparkles, BookOpen, Loader2 } from 'lucide-react'
import { spendCores, hasEnoughCores, AI_HINT_COSTS, type CoreSpendCategory } from '@/lib/api/core'

interface AIHintButtonProps {
  hintType: 'light' | 'medium' | 'deep'
  currentBalance: number
  onHintPurchased: (result: { category: CoreSpendCategory; amount: number }) => void
  disabled?: boolean
  lang?: 'zh' | 'en'
}

const HINT_CONFIG = {
  light: {
    icon: Lightbulb,
    label: { zh: '轻度提示', en: 'Light Hint' },
    description: { zh: '获取思路方向', en: 'Get direction hint' },
  },
  medium: {
    icon: Sparkles,
    label: { zh: '中度提示', en: 'Medium Hint' },
    description: { zh: '获取关键步骤', en: 'Get key steps' },
  },
  deep: {
    icon: BookOpen,
    label: { zh: '深度解析', en: 'Deep Analysis' },
    description: { zh: '完整解题思路', en: 'Full solution' },
  },
}

export function AIHintButton({
  hintType,
  currentBalance,
  onHintPurchased,
  disabled = false,
  lang = 'zh',
}: AIHintButtonProps) {
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)

  const config = HINT_CONFIG[hintType]
  const Icon = config.icon
  const cost = AI_HINT_COSTS[hintType]
  const canAfford = hasEnoughCores(currentBalance, hintType)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const purchaseHint = async () => {
    if (!canAfford || isPending) return

    startTransition(async () => {
      setError(null)
      try {
        const category = `ai_hint_${hintType}` as CoreSpendCategory
        const result = await spendCores({
          amount: cost,
          category,
          description: config.label[lang as 'zh' | 'en'],
        })

        onHintPurchased({ category, amount: cost })
      } catch (err) {
        setError(err instanceof Error ? err.message : t('消耗失败', 'Failed to spend'))
      }
    })
  }

  return (
    <div className="relative">
      <button type="button"
        onClick={purchaseHint}
        disabled={disabled || !canAfford || isPending}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all
          ${canAfford && !disabled
            ? 'bg-purple-500/10 hover:bg-purple-500/20 text-purple-600 dark:text-purple-400 border border-purple-500/30'
            : 'bg-muted/50 text-muted-foreground cursor-not-allowed'
          }
        `}
      >
        {isPending ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Icon className="size-4" />
        )}
        <span>{t(config.label.zh, config.label.en)}</span>
        <div className="flex items-center gap-0.5 ml-1 px-2 py-0.5 bg-purple-500/20 rounded-full">
          <Gem className="size-3" />
          <span className="text-xs">{cost}</span>
        </div>
      </button>

      {!canAfford && (
        <div className="absolute -bottom-6 left-0 right-0 text-center">
          <span className="text-xs text-red-500">{t('智核不足', 'Insufficient cores')}</span>
        </div>
      )}

      {error && (
        <div className="absolute -bottom-6 left-0 right-0 text-center">
          <span className="text-xs text-red-500">{error}</span>
        </div>
      )}
    </div>
  )
}

// Combined hint panel with all three options
interface AIHintPanelProps {
  currentBalance: number
  onHintPurchased: (result: { category: CoreSpendCategory; amount: number }) => void
  disabled?: boolean
  lang?: 'zh' | 'en'
}

export function AIHintPanel({ currentBalance, onHintPurchased, disabled = false, lang = 'zh' }: AIHintPanelProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  return (
    <div className="bg-card rounded-xl border border-border p-4">
      <div className="flex items-center gap-2 mb-3">
        <Gem className="size-5 text-purple-500" />
        <h3 className="font-medium text-foreground">{t('AI 提示', 'AI Hints')}</h3>
        <div className="ml-auto flex items-center gap-1 text-sm text-muted-foreground">
          <Gem className="size-3 text-purple-500" />
          <span>{currentBalance}</span>
        </div>
      </div>

      <div className="flex flex-col gap-y-2 text-xs text-muted-foreground mb-3">
        <p>{t('使用智核获取AI提示，帮助你更好地理解题目', 'Use cores to get AI hints and better understand the problem')}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(['light', 'medium', 'deep'] as const).map((type) => (
          <AIHintButton
            key={type}
            hintType={type}
            currentBalance={currentBalance}
            onHintPurchased={onHintPurchased}
            disabled={disabled}
            lang={lang}
          />
        ))}
      </div>
    </div>
  )
}
