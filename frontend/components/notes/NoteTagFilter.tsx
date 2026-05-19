'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, Plus } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { getNoteTags, createNoteTag, deleteNoteTag } from '@/lib/api/notes'
import type { NoteTagResponse } from '@/types/api'

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

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
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
    if (!confirm(t('确定要删除这个标签吗？', 'Are you sure you want to delete this tag?'))) {
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
  }, [selectedTags, t, onTagsChange])

  const toggleTag = useCallback((tagName: string) => {
    onTagsChange(
      selectedTags.includes(tagName)
        ? selectedTags.filter((t) => t !== tagName)
        : [...selectedTags, tagName]
    )
  }, [selectedTags, onTagsChange])

  return (
    <div className="gap-y-4">
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
                <button type="button"
                  onClick={() => toggleTag(tagName)}
                  className="hover:text-primary/70"
                >
                  <X className="size-4" />
                </button>
              </span>
            )
          })}
          <button type="button"
            onClick={() => onTagsChange([])}
            className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-full transition-colors"
          >
            {t('清除', 'Clear')}
          </button>
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
                  <button type="button"
                    onClick={() => toggleTag(tag.name)}
                    className="flex items-center gap-1"
                  >
                    <Plus className="size-4" />
                    {tag.name}
                  </button>
                  <button type="button"
                    onClick={() => handleDeleteTag(tag.id, tag.name)}
                    className="ml-1 opacity-0 group-hover:opacity-100 hover:text-destructive transition-opacity"
                    title={t('删除标签', 'Delete tag')}
                  >
                    <X className="size-3.5" />
                  </button>
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
          placeholder={t('新建标签...', 'New tag...')}
          className="flex-1 px-4 py-2 text-sm border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
        />
        <button type="button"
          onClick={handleCreateTag}
          disabled={isCreating || !newTagName.trim()}
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {t('添加', 'Add')}
        </button>
      </div>
    </div>
  )
}
