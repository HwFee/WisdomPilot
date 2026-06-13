'use client'

import { Save, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
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
  const canSave = !isSaving && !!content.trim()
  const saveLabel = isSaving ? translate(lang, '保存中...', 'Saving...') : translate(lang, '保存笔记', 'Save note')

  return (
    <footer className="border-t border-border px-6 py-4 bg-card flex items-center justify-between gap-4">
      <div className="text-sm text-muted-foreground hidden sm:block">
        {translate(lang, '支持 Markdown、数学公式与代码高亮', 'Markdown, math and code highlighting supported')}
      </div>
      <div className="flex items-center gap-3 ml-auto">
        {onCancel && (
          <Button variant="outline" size="sm" onClick={onCancel} disabled={isSaving}>
            <X className="size-4 mr-1.5" strokeWidth={1.5} />
            {translate(lang, '取消', 'Cancel')}
          </Button>
        )}
        <Button type="button" size="sm" onClick={onSave} disabled={!canSave} className="gap-2">
          <Save className="size-4" strokeWidth={1.5} />
          {saveLabel}
        </Button>
      </div>
    </footer>
  )
}
