'use client'

import { Save } from 'lucide-react'
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
  const saveLabel = isSaving ? translate(lang, '保存中...', 'Saving...') : translate(lang, '保存', 'Save')

  if (variant === 'fullPage') {
    return (
      <footer className="border-t border-border px-6 py-4">
        <Button type="button" onClick={onSave} disabled={!canSave} className="w-full gap-2">
          <Save className="size-4" />
          {saveLabel}
        </Button>
      </footer>
    )
  }

  return (
    <footer className="flex items-center justify-between border-t border-border px-6 py-4">
      <div className="text-sm text-muted-foreground">
        {translate(lang, '支持 Markdown，数学公式 $...$ 和代码高亮', 'Markdown, math $...$ and code highlighting')}
      </div>
      <div className="flex gap-3">
        <Button variant="outline" onClick={onCancel}>
          {translate(lang, '取消', 'Cancel')}
        </Button>
        <Button type="button" onClick={onSave} disabled={!canSave} className="gap-2">
          <Save className="size-4" />
          {saveLabel}
        </Button>
      </div>
    </footer>
  )
}
