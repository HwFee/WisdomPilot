'use client'

import { cn } from '@/lib/utils'

interface LocalFirstToggleProps {
  checked: boolean
  onChange: (v: boolean) => void
}

export function LocalFirstToggle({ checked, onChange }: LocalFirstToggleProps) {
  return (
    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
      <div>
        <div className="text-sm font-medium">本地优先模式</div>
        <div className="text-xs text-muted-foreground">优先使用本地模型，本地不可用时 fallback 到云端</div>
      </div>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        aria-label="本地优先模式开关"
        className={cn(
          'relative w-11 h-6 rounded-full transition-colors',
          checked ? 'bg-primary' : 'bg-muted-foreground/30'
        )}
      >
        <span className={cn(
          'absolute top-1 left-1 size-4 bg-white rounded-full transition-transform',
          checked && 'translate-x-5'
        )} />
      </button>
    </div>
  )
}
