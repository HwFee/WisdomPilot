'use client'

import { Eye } from 'lucide-react'
import { MarkdownRenderer } from '@/components/editor/MarkdownRenderer'
import { translate } from './note-translate'

interface MarkdownPreviewPaneProps {
  content: string
  lang: 'zh' | 'en'
  variant: 'fullPage' | 'modal'
}

export function MarkdownPreviewPane({ content, lang, variant }: MarkdownPreviewPaneProps) {
  const proseClass = variant === 'fullPage' ? 'prose prose-lg' : 'prose prose-sm'

  if (variant === 'fullPage') {
    return (
      <div className="flex-1 flex flex-col min-w-0 bg-card">
        <div className="flex items-center justify-between px-4 py-2 text-xs font-medium uppercase tracking-[1.5px] text-muted-foreground border-b border-border bg-muted/20">
          <div className="flex items-center gap-2">
            <Eye className="size-3.5" strokeWidth={1.5} />
            <span>{translate(lang, '预览', 'Preview')}</span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <div className={`${proseClass} dark:prose-invert max-w-none`}>
            <MarkdownRenderer content={content} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="flex items-center justify-center mb-2 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Eye className="size-4" strokeWidth={1.5} />
          <span>{translate(lang, '预览', 'Preview')}</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 border border-border">
        <div className={`${proseClass} dark:prose-invert max-w-none`}>
          {content ? <MarkdownRenderer content={content} /> : null}
        </div>
      </div>
    </div>
  )
}
