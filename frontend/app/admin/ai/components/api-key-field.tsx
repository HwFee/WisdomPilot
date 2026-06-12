'use client'

import { Pencil, Trash2 } from 'lucide-react'

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
  preview,
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
            <div className="flex-1 px-3 py-2 border border-border rounded-lg text-sm bg-muted/50 text-muted-foreground font-mono tracking-widest overflow-hidden text-ellipsis whitespace-nowrap">
              {maskedPreview}
            </div>
            <button
              type="button"
              onClick={onEnterReplace}
              className="flex items-center gap-1 px-3 py-2 text-sm border border-primary text-primary rounded-lg hover:bg-primary/10 transition-colors shrink-0"
            >
              <Pencil className="size-3.5" />
              替换
            </button>
            <button
              type="button"
              onClick={onDelete}
              className="flex items-center gap-1 px-3 py-2 text-sm border border-red-300 text-red-500 rounded-lg hover:bg-red-50 transition-colors shrink-0"
            >
              <Trash2 className="size-3.5" />
            </button>
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
            <button
              type="button"
              onClick={onCancelReplace}
              className="px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors shrink-0"
            >
              取消
            </button>
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
