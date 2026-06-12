'use client'

import { X, Tags, Minimize2 } from 'lucide-react'
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

  if (variant === 'fullPage') {
    return (
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onToggleTagSelector}>
            <Tags className="size-4 mr-1.5" strokeWidth={1.5} />
            {translate(lang, '标签', 'Tags')}
          </Button>
          {onClose && (
            <Button variant="ghost" size="icon" onClick={onClose} aria-label={translate(lang, '关闭', 'Close')}>
              <Minimize2 className="size-4" strokeWidth={1.5} />
            </Button>
          )}
        </div>
      </header>
    )
  }

  return (
    <header className="flex items-center justify-between border-b border-border px-6 py-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={onToggleTagSelector}>
          <Tags className="size-4 mr-1.5" strokeWidth={1.5} />
          {translate(lang, '标签', 'Tags')}
        </Button>
        <Button variant="ghost" size="icon" onClick={onClose} aria-label={translate(lang, '关闭', 'Close')}>
          <X className="size-4" strokeWidth={1.5} />
        </Button>
      </div>
    </header>
  )
}
