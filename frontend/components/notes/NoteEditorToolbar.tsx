'use client'

import { X, Tags, Minimize2 } from 'lucide-react'
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
  if (variant === 'fullPage') {
    return (
      <div className="flex items-center justify-between px-6 py-4 border-b bg-muted/30">
        <h2 className="text-lg font-semibold">
          {note ? translate(lang, '编辑笔记', 'Edit Note') : translate(lang, '新建笔记', 'New Note')}
        </h2>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onToggleTagSelector}
            className="flex items-center gap-2 px-3 py-2 hover:bg-muted rounded-lg transition-colors text-sm"
            title={translate(lang, '管理标签', 'Manage Tags')}
          >
            <Tags className="size-4" />
            <span>{translate(lang, '标签', 'Tags')}</span>
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
              title={translate(lang, '关闭', 'Close')}
            >
              <Minimize2 className="size-5" />
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between p-5 border-b">
      <h2 className="text-xl font-semibold">
        {note ? translate(lang, '编辑笔记', 'Edit Note') : translate(lang, '新建笔记', 'New Note')}
      </h2>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleTagSelector}
          className="flex items-center gap-2 px-3 py-2 hover:bg-muted rounded-lg transition-colors"
          title={translate(lang, '管理标签', 'Manage Tags')}
        >
          <Tags className="size-5" />
          <span className="text-sm">{translate(lang, '标签', 'Tags')}</span>
        </button>
        <button
          type="button"
          onClick={onClose}
          className="p-2 hover:bg-muted rounded-lg transition-colors"
        >
          <X className="size-5" />
        </button>
      </div>
    </div>
  )
}
