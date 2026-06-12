'use client'

import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
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
  return (
    <div className="border-b border-border px-6 py-4">
      <div className="flex flex-wrap gap-2 mb-4">
        {selectedTags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 border border-border px-3 py-1.5 text-sm text-foreground"
          >
            {tag}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => onToggleTag(tag)}
              className="size-5 -mr-1"
              aria-label={translate(lang, `取消选择 ${tag}`, `Deselect ${tag}`)}
            >
              <X className="size-3.5" strokeWidth={1.5} />
            </Button>
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
          className="flex-1 h-9 px-3 text-sm bg-background border border-border focus:outline-none focus:border-foreground"
        />
        <Button type="button" size="sm" onClick={onCreateTag}>
          {translate(lang, '创建', 'Create')}
        </Button>
      </div>
      <div className="flex flex-wrap gap-2">
        {(() => {
          const items = []
          for (const tag of availableTags) {
            if (selectedTagSet.has(tag.name)) continue
            items.push(
              <Button
                type="button"
                key={tag.id}
                variant="ghost"
                size="sm"
                onClick={() => onToggleTag(tag.name)}
                className="border border-border rounded-full px-3"
                style={{ borderColor: tag.color }}
              >
                {tag.name}
              </Button>
            )
          }
          return items
        })()}
      </div>
    </div>
  )
}
