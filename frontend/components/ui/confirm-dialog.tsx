'use client'

import { AlertTriangle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Panel, PanelHeader } from '@/components/layout'
import { cn } from '@/lib/utils'

interface ConfirmDialogProps {
  isOpen: boolean
  title?: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'default'
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  isOpen,
  title = '确认操作',
  description = '确定要继续吗？',
  confirmLabel = '确认',
  cancelLabel = '取消',
  variant = 'default',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-4"
      onClick={onCancel}
    >
      <Panel
        className={cn('w-full max-w-md overflow-hidden', variant === 'danger' && 'border-t-2 border-t-red-500')}
        onClick={(e) => e.stopPropagation()}
      >
        <PanelHeader
          title={title}
          action={
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={onCancel}
              aria-label="关闭"
            >
              <X className="size-4" strokeWidth={1.5} />
            </Button>
          }
        />
        <div className="p-6">
          <div className="flex items-start gap-4">
            {variant === 'danger' && (
              <div className="size-10 shrink-0 bg-red-50 border border-red-200 flex items-center justify-center">
                <AlertTriangle className="size-5 text-red-500" strokeWidth={1.5} />
              </div>
            )}
            <p className="text-sm text-muted-foreground leading-relaxed">
              {description}
            </p>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" size="sm" onClick={onCancel}>
              {cancelLabel}
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={onConfirm}
              className={cn(variant === 'danger' && 'bg-red-500 hover:bg-red-600 text-white')}
            >
              {confirmLabel}
            </Button>
          </div>
        </div>
      </Panel>
    </div>
  )
}
