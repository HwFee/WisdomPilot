'use client'

import { Save } from 'lucide-react'
import { translate } from './note-translate'

interface NoteEditorFooterProps {
  isSaving: boolean
  content: string
  lang: 'zh' | 'en'
  onSave: () => void
  onCancel?: () => void
  variant: 'fullPage' | 'modal'
}

export function NoteEditorFooter({
  isSaving,
  content,
  lang,
  onSave,
  onCancel,
  variant,
}: NoteEditorFooterProps) {
  if (variant === 'fullPage') {
    return (
      <div className="px-6 py-3 border-t border-border bg-muted/30">
        <button
          type="button"
          onClick={onSave}
          disabled={isSaving || !content.trim()}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <Save className="size-4" />
          {isSaving ? translate(lang, '保存中...', 'Saving...') : translate(lang, '保存', 'Save')}
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between p-5 border-t bg-muted/30">
      <div className="text-sm text-muted-foreground">
        {translate(lang, '支持 Markdown，数学公式 $...$ 和代码高亮', 'Markdown, math $...$ and code highlighting')}
      </div>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-5 py-2.5 text-sm border-2 rounded-xl hover:bg-muted transition-colors"
        >
          {translate(lang, '取消', 'Cancel')}
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={isSaving || !content.trim()}
          className="px-5 py-2.5 text-sm bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          <Save className="size-4" />
          {isSaving ? translate(lang, '保存中...', 'Saving...') : translate(lang, '保存', 'Save')}
        </button>
      </div>
    </div>
  )
}
