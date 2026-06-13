'use client'

import { X, Tags, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { translate } from './note-translate'
import type { NoteResponse } from '@/types/api'

interface NoteEditorToolbarProps {
  note?: NoteResponse | null
  lang: 'zh' | 'en'
  showTagSelector: boolean
  onToggleTagSelector: () => void
  onClose?: () => void
  variant: 'fullPage' | 'modal'
}

export function NoteEditorToolbar({
  note,
  lang,
  showTagSelector,
  onToggleTagSelector,
  onClose,
  variant,
}: NoteEditorToolbarProps) {
  const title = note ? translate(lang, '编辑笔记', 'Edit Note') : translate(lang, '新建笔记', 'New Note')

  return (
    <header className="flex items-center justify-between border-b border-border px-6 py-4 bg-card">
      <div className="flex items-center gap-3 min-w-0">
        {variant === 'fullPage' && onClose && (
          <Button variant="ghost" size="icon" onClick={onClose} aria-label={translate(lang, '返回', 'Back')} className="shrink-0">
            <ArrowLeft className="size-5" strokeWidth={1.5} />
          </Button>
        )}
        <h2 className="text-base font-semibold uppercase tracking-[1.5px] truncate">{title}</h2>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Button
          variant={showTagSelector ? 'secondary' : 'ghost'}
          size="sm"
          onClick={onToggleTagSelector}
          className="gap-1.5"
        >
          <Tags className="size-4" strokeWidth={1.5} />
          {translate(lang, '标签', 'Tags')}
        </Button>
        {variant === 'modal' && onClose && (
          <Button variant="ghost" size="icon" onClick={onClose} aria-label={translate(lang, '关闭', 'Close')}>
            <X className="size-5" strokeWidth={1.5} />
          </Button>
        )}
      </div>
    </header>
  )
}
