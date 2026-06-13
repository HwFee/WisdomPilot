'use client'

import { X, Plus } from 'lucide-react'
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
}: NoteTagSelectorProps) {
  const t = (zh: string, en: string) => translate(lang, zh, en)

  return (
    <div className="border-b border-border px-6 py-4 bg-muted/20">
      <div className="flex flex-col gap-4">
        {/* Selected tags */}
        {selectedTags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {selectedTags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 border border-border bg-card px-3 py-1.5 text-sm text-foreground"
              >
                {tag}
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => onToggleTag(tag)}
                  className="size-5 -mr-1"
                  aria-label={t(`取消选择 ${tag}`, `Deselect ${tag}`)}
                >
                  <X className="size-3.5" strokeWidth={1.5} />
                </Button>
              </span>
            ))}
          </div>
        )}

        {/* Create new tag */}
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={newTagName}
            onChange={(e) => onNewTagNameChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onCreateTag()}
            placeholder={t('输入新标签名', 'New tag name')}
            aria-label={t('新标签名', 'New tag name')}
            className="flex-1 h-9 px-3 text-sm bg-background border border-border focus:outline-none focus:border-foreground transition-colors"
          />
          <Button type="button" size="sm" onClick={onCreateTag} disabled={!newTagName.trim()} className="gap-1.5">
            <Plus className="size-4" strokeWidth={1.5} />
            {t('创建标签', 'Create tag')}
          </Button>
        </div>

        {/* Available tags */}
        {availableTags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {availableTags.map((tag) => {
              if (selectedTagSet.has(tag.name)) return null
              return (
                <Button
                  type="button"
                  key={tag.id}
                  variant="outline"
                  size="sm"
                  onClick={() => onToggleTag(tag.name)}
                  className="h-8 px-3 gap-1"
                  style={{ borderColor: tag.color }}
                >
                  <span className="size-2 rounded-full" style={{ backgroundColor: tag.color }} />
                  {tag.name}
                </Button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
