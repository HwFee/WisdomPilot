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
      <div className="flex-1 flex flex-col min-w-0 border-r">
        <div className="flex items-center justify-center px-6 py-3 bg-muted/50 text-sm text-muted-foreground border-b border-border">
          <div className="flex items-center gap-2">
            <Edit3 className="size-4" />
            <span>{translate(lang, 'Markdown 编辑器', 'Markdown Editor')}</span>
          </div>
        </div>
        <textarea
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
          placeholder={translate(
            lang,
            '使用 Markdown 编写，支持数学公式和代码高亮...',
            'Write in Markdown with math and code support...'
          )}
          aria-label={translate(lang, '笔记内容', 'Note content')}
          className="flex-1 w-full p-6 resize-none bg-background font-mono text-base leading-relaxed focus:outline-none"
        />
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="flex items-center justify-center mb-2 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Edit3 className="size-4" />
          <span>{translate(lang, '编辑', 'Edit')}</span>
        </div>
      </div>
      <textarea
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
        placeholder={translate(lang, '使用 Markdown 编写...', 'Write in Markdown...')}
        aria-label={translate(lang, '笔记内容', 'Note content')}
        className="flex-1 w-full p-4 resize-none rounded-xl border border-border bg-muted/30 font-mono text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary"
      />
    </div>
  )
}
