'use client'

import { Pencil, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ApiKeyFieldProps {
  label: string
  hasKey: boolean
  preview: string
  keyLength: number
  value: string
  onChange: (v: string) => void
  replaceMode: boolean
  onEnterReplace: () => void
  onCancelReplace: () => void
  onDelete: () => void
  placeholder?: string
}

export function ApiKeyField({
  label,
  hasKey,
  keyLength,
  value,
  onChange,
  replaceMode,
  onEnterReplace,
  onCancelReplace,
  onDelete,
  placeholder,
}: ApiKeyFieldProps) {
  const maskedPreview = hasKey && keyLength > 0 ? `${'•'.repeat(keyLength)}` : ''

  return (
    <div className="flex flex-col gap-y-2">
      <div className="flex items-center gap-2">
        {hasKey && !replaceMode ? (
          <>
            <div className="flex-1 px-3 py-2 border border-border rounded-lg text-sm bg-muted text-muted-foreground font-mono tracking-widest overflow-hidden text-ellipsis whitespace-nowrap">
              {maskedPreview}
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onEnterReplace}
              className="flex items-center gap-1 border-primary text-primary hover:bg-primary/10 shrink-0"
            >
              <Pencil className="size-3.5" />
              替换
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={onDelete}
              className="size-auto p-2 text-destructive hover:bg-destructive/10 hover:text-destructive shrink-0"
              aria-label="删除 API 密钥"
            >
              <Trash2 className="size-3.5" />
            </Button>
          </>
        ) : !replaceMode ? (
          <input
            type="text"
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder || '输入 API 密钥'}
            aria-label={label || 'API 密钥'}
            className="flex-1 px-3 py-2 border border-border rounded-lg text-sm bg-background font-mono focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        ) : (
          <>
            <input
              type="text"
              value={value}
              onChange={e => onChange(e.target.value)}
              placeholder={placeholder || '输入新密钥'}
              aria-label={label || 'API 密钥'}
              data-autofocus="true"
              className="flex-1 px-3 py-2 border border-border rounded-lg text-sm bg-background font-mono focus:ring-2 focus:ring-primary focus:border-transparent"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onCancelReplace}
              className="shrink-0"
            >
              取消
            </Button>
          </>
        )}
      </div>
      {replaceMode && (
        <p className="text-xs text-muted-foreground">
          {value ? `将替换为新密钥（${value.length} 位）` : '输入为空将删除现有密钥'}
        </p>
      )}
    </div>
  )
}
