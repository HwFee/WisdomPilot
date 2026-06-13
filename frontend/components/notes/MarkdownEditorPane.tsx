'use client'

import { Edit3 } from 'lucide-react'
import { translate } from './note-translate'

interface MarkdownEditorPaneProps {
  content: string
  lang: 'zh' | 'en'
  onContentChange: (value: string) => void
  variant: 'fullPage' | 'modal'
}

export function MarkdownEditorPane({
  content,
  lang,
  onContentChange,
  variant,
}: MarkdownEditorPaneProps) {
  if (variant === 'fullPage') {
    return (
      <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-card">
        <div className="flex items-center justify-between px-4 py-2 text-xs font-medium uppercase tracking-[1.5px] text-muted-foreground border-b border-border bg-muted/20">
          <div className="flex items-center gap-2">
            <Edit3 className="size-3.5" strokeWidth={1.5} />
            <span>{translate(lang, '编辑', 'Edit')}</span>
          </div>
          <span className="text-[10px] normal-case tracking-normal">Markdown</span>
        </div>
        <textarea
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
          placeholder={translate(lang, '开始编写笔记内容...', 'Start writing note content...')}
          aria-label={translate(lang, '笔记内容', 'Note content')}
          className="flex-1 w-full p-6 resize-none bg-transparent font-mono text-base leading-relaxed focus:outline-none"
        />
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="flex items-center justify-center mb-2 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Edit3 className="size-4" strokeWidth={1.5} />
          <span>{translate(lang, '编辑', 'Edit')}</span>
        </div>
      </div>
      <textarea
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
        placeholder={translate(lang, '使用 Markdown 编写...', 'Write in Markdown...')}
        aria-label={translate(lang, '笔记内容', 'Note content')}
        className="flex-1 w-full p-4 resize-none bg-background border border-border font-mono text-sm leading-relaxed focus:outline-none focus:border-foreground"
      />
    </div>
  )
}
