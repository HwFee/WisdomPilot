'use client'

import { Type } from 'lucide-react'
import { translate } from './note-translate'

interface NoteTitleInputProps {
  title: string
  lang: 'zh' | 'en'
  onTitleChange: (value: string) => void
  variant: 'fullPage' | 'modal'
}

export function NoteTitleInput({ title, lang, onTitleChange, variant }: NoteTitleInputProps) {
  return (
    <div className="border-b border-border px-6 py-4 bg-card">
      <div className="flex items-center gap-3">
        <Type className="size-5 text-muted-foreground shrink-0" strokeWidth={1.5} />
        <input
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder={translate(lang, '输入笔记标题...', 'Enter note title...')}
          aria-label={translate(lang, '笔记标题', 'Note title')}
          className="flex-1 bg-transparent text-xl font-semibold text-foreground placeholder:text-muted-foreground py-1 focus:outline-none"
        />
      </div>
    </div>
  )
}
