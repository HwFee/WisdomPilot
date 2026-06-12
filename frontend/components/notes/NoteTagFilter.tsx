'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getStoredToken } from '@/lib/api'
import { getNoteTags, createNoteTag, deleteNoteTag } from '@/lib/api/notes'
import type { NoteTagResponse } from '@/types/api'

function translate(lang: 'zh' | 'en', zh: string, en: string) {
  return lang === 'zh' ? zh : en
}

interface NoteTagFilterProps {
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  lang?: 'zh' | 'en'
}

export function NoteTagFilter({
  selectedTags,
  onTagsChange,
  lang = 'zh',
}: NoteTagFilterProps) {
  const [tags, setTags] = useState<NoteTagResponse[]>([])
  const [newTagName, setNewTagName] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const selectedTagSet = new Set(selectedTags)

  // Load tags
  const loadTags = useCallback(async () => {
    const token = getStoredToken()
    if (!token) return
    try {
      const data = await getNoteTags(token)
      setTags(data.tags)
    } catch {
      // Silently handle
    }
  }, [])

  useEffect(() => {
    // react-doctor-disable-next-line no-derived-state, react-doctor/no-derived-state — tags are fetched from the API and are not derivable from props/state
    loadTags()
  }, [loadTags])

  const handleCreateTag = useCallback(async () => {
    if (!newTagName.trim()) return

    const token = getStoredToken()
    if (!token) return

    setIsCreating(true)
    try {
      const randomColor = `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`
      const tag = await createNoteTag(token, {
        name: newTagName.trim(),
        color: randomColor,
      })
      setTags((prev) => [...prev, tag])
      setNewTagName('')
    } catch (error) {
      console.error('[标签] 创建失败:', error)
    } finally {
      setIsCreating(false)
    }
  }, [newTagName])

  const handleDeleteTag = useCallback(async (tagId: string, tagName: string) => {
    if (!confirm(translate(lang, '确定要删除这个标签吗？', 'Are you sure you want to delete this tag?'))) {
      return
    }

    const token = getStoredToken()
    if (!token) return

    try {
      await deleteNoteTag(token, tagId)
      setTags((prev) => prev.filter((t) => t.id !== tagId))
      onTagsChange(selectedTags.filter((t) => t !== tagName))
    } catch (error) {
      console.error('[标签] 删除失败:', error)
    }
  }, [selectedTags, lang, onTagsChange])

  const toggleTag = useCallback((tagName: string) => {
    onTagsChange(
      selectedTags.includes(tagName)
        ? selectedTags.filter((t) => t !== tagName)
        : [...selectedTags, tagName]
    )
  }, [selectedTags, onTagsChange])

  return (
    <div className="flex flex-col gap-y-4">
      {/* Selected tags */}
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedTags.map((tagName) => {
            const tag = tags.find((t) => t.name === tagName)
            return (
              <span
                key={tagName}
                className="px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-full flex items-center gap-2"
                style={{ borderColor: tag?.color }}
              >
                {tagName}
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => toggleTag(tagName)}
                  className="size-5 hover:text-primary/70"
                  aria-label={translate(lang, '取消选择', 'Deselect')}
                >
                  <X className="size-4" />
                </Button>
              </span>
            )
          })}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => onTagsChange([])}
            className="rounded-full"
          >
            {translate(lang, '清除', 'Clear')}
          </Button>
        </div>
      )}

      {/* Available tags */}
      <div className="flex flex-wrap gap-2">
        {tags.flatMap((tag) =>
          selectedTagSet.has(tag.name)
            ? []
            : [
                <span
                  key={tag.id}
                  className="group px-3 py-1.5 text-sm border-2 rounded-full flex items-center gap-1 hover:bg-muted transition-colors"
                  style={{ borderColor: tag.color }}
                >
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleTag(tag.name)}
                    className="h-auto p-0 px-0 gap-1"
                  >
                    <Plus className="size-4" />
                    {tag.name}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteTag(tag.id, tag.name)}
                    className="ml-1 size-5 opacity-0 group-hover:opacity-100 hover:text-destructive transition-opacity"
                    title={translate(lang, '删除标签', 'Delete tag')}
                    aria-label={translate(lang, '删除标签', 'Delete tag')}
                  >
                    <X className="size-3.5" />
                  </Button>
                </span>,
              ]
        )}
      </div>

      {/* Create new tag */}
      <div className="flex gap-3 pt-3 border-t">
        <input
          type="text"
          value={newTagName}
          onChange={(e) => setNewTagName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreateTag()}
          placeholder={translate(lang, '新建标签...', 'New tag...')}
          aria-label={translate(lang, '新建标签', 'New tag')}
          className="flex-1 px-4 py-2 text-sm border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
        />
        <Button
          type="button"
          onClick={handleCreateTag}
          disabled={isCreating || !newTagName.trim()}
        >
          {translate(lang, '添加', 'Add')}
        </Button>
      </div>
    </div>
  )
}
