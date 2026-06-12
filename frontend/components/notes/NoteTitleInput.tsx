'use client'

import { translate } from './note-translate'

interface NoteTitleInputProps {
  title: string
  lang: 'zh' | 'en'
  onTitleChange: (value: string) => void
  variant: 'fullPage' | 'modal'
}

export function NoteTitleInput({ title, lang, onTitleChange, variant }: NoteTitleInputProps) {
  return (
    <div className="border-b border-border px-6 py-4">
      <input
        type="text"
        value={title}
        onChange={(e) => onTitleChange(e.target.value)}
        placeholder={translate(lang, '笔记标题（可选）', 'Note title (optional)')}
        aria-label={translate(lang, '笔记标题', 'Note title')}
        className="w-full bg-background text-2xl font-semibold text-foreground placeholder:text-muted-foreground py-2 border-b border-transparent focus:outline-none focus:border-foreground transition-colors"
      />
    </div>
  )
}
