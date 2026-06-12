'use client'

import { translate } from './note-translate'

interface NoteTitleInputProps {
  title: string
  lang: 'zh' | 'en'
  onTitleChange: (value: string) => void
  variant: 'fullPage' | 'modal'
}

export function NoteTitleInput({ title, lang, onTitleChange, variant }: NoteTitleInputProps) {
  const wrapperClass = variant === 'fullPage' ? 'px-6 py-4 border-b' : 'px-5 py-4 border-b'

  return (
    <div className={wrapperClass}>
      <input
        type="text"
        value={title}
        onChange={(e) => onTitleChange(e.target.value)}
        placeholder={translate(lang, '笔记标题（可选）', 'Note title (optional)')}
        aria-label={translate(lang, '笔记标题', 'Note title')}
        className="w-full px-4 py-3 text-xl font-medium border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
      />
    </div>
  )
}
