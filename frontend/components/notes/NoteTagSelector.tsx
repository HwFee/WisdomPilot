'use client'

import { X } from 'lucide-react'
import type { ReactNode } from 'react'
import { translate } from './note-translate'
import type { NoteTagResponse } from '@/types/api'

interface NoteTagSelectorProps {
  selectedTags: string[]
  selectedTagSet: Set<string>
  availableTags: NoteTagResponse[]
  newTagName: string
  lang: 'zh' | 'en'
  onNewTagNameChange: (value: string) => void
  onCreateTag: () => void
  onToggleTag: (tagName: string) => void
  variant: 'fullPage' | 'modal'
}

export function NoteTagSelector({
  selectedTags,
  selectedTagSet,
  availableTags,
  newTagName,
  lang,
  onNewTagNameChange,
  onCreateTag,
  onToggleTag,
  variant,
}: NoteTagSelectorProps) {
  const containerClass =
    variant === 'fullPage'
      ? 'px-6 py-4 border-b bg-muted/30'
      : 'px-5 py-4 border-b bg-muted/30'

  return (
    <div className={containerClass}>
      <div className="flex flex-wrap gap-2 mb-4">
        {selectedTags.map((tag) => (
          <span
            key={tag}
            className="px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-full flex items-center gap-2"
          >
            {tag}
            <button
              type="button"
              onClick={() => onToggleTag(tag)}
              className="hover:text-primary/70"
            >
              <X className={variant === 'fullPage' ? 'size-3.5' : 'size-4'} />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          value={newTagName}
          onChange={(e) => onNewTagNameChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onCreateTag()}
          placeholder={translate(lang, '输入新标签名', 'New tag name')}
          aria-label={translate(lang, '新标签名', 'New tag name')}
          className="flex-1 px-4 py-2 text-sm border rounded-lg bg-background"
        />
        <button
          type="button"
          onClick={onCreateTag}
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
        >
          {translate(lang, '创建', 'Create')}
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {(() => {
          const tagButtons: ReactNode[] = []
          for (const tag of availableTags) {
            if (selectedTagSet.has(tag.name)) continue
            tagButtons.push(
              <button
                type="button"
                key={tag.id}
                onClick={() => onToggleTag(tag.name)}
                className="px-3 py-1.5 text-sm border-2 rounded-full hover:bg-muted transition-colors"
                style={{ borderColor: tag.color }}
              >
                {tag.name}
              </button>
            )
          }
          return tagButtons
        })()}
      </div>
    </div>
  )
}
