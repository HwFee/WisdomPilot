'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { getStoredToken } from '@/lib/api'
import { createNote, updateNote, createNoteTag, getNoteTags } from '@/lib/api/notes'
import { NoteEditorFullPage } from './NoteEditorFullPage'
import { NoteEditorModal } from './NoteEditorModal'
import { translate } from './note-translate'
import type { NoteCreate, NoteResponse, NoteTagResponse } from '@/types/api'

const EMPTY_STRING_ARRAY: string[] = []

interface NoteEditorProps {
  note?: NoteResponse | null
  exerciseId?: number
  chapterId?: number
  sectionId?: number
  courseId?: number
  subsectionIndex?: number
  knowledgePoints?: string[]
  prefillContent?: string
  prefillTitle?: string
  source?: 'manual' | 'ai_answer' | 'question'
  onSave?: (note: NoteResponse) => void
  onClose?: () => void
  lang?: 'zh' | 'en'
  /** 完整页面模式 - 用于笔记页面，启用分屏预览 */
  isFullPage?: boolean
}

export function NoteEditor({
  note,
  exerciseId,
  chapterId,
  sectionId,
  courseId,
  subsectionIndex = 0,
  knowledgePoints = EMPTY_STRING_ARRAY,
  prefillContent,
  prefillTitle,
  source = 'manual',
  onSave,
  onClose,
  lang = 'zh',
  isFullPage = false,
}: NoteEditorProps) {
  const [noteState, setNoteState] = useState({
    title: note?.title || prefillTitle || '',
    content: note?.content || prefillContent || '',
    selectedTags: note?.tags || ([] as string[]),
  })
  const [availableTags, setAvailableTags] = useState<NoteTagResponse[]>([])
  const [tagUi, setTagUi] = useState({ newTagName: '', showTagSelector: false })
  const { title, content, selectedTags } = noteState
  const { newTagName, showTagSelector } = tagUi
  const [isSaving, setIsSaving] = useState(false)

  const selectedTagSet = useMemo(() => new Set(noteState.selectedTags), [noteState.selectedTags])

  // Load available tags
  useEffect(() => {
    const loadTags = async () => {
      const token = getStoredToken()
      if (!token) return
      try {
        const data = await getNoteTags(token)
        setAvailableTags(data.tags)
      } catch {
        // Silently handle
      }
    }
    loadTags()
  }, [])

  const handleSave = useCallback(async () => {
    const token = getStoredToken()
    if (!token) return

    setIsSaving(true)
    try {
      let savedNote: NoteResponse

      if (note) {
        // Update existing note
        savedNote = await updateNote(token, note.id, {
          title: noteState.title || undefined,
          content: noteState.content,
          tags: noteState.selectedTags,
          knowledge_points: knowledgePoints,
        })
      } else {
        // Create new note
        const noteData: NoteCreate = {
          title: noteState.title || `${translate(lang, '笔记', 'Note')} ${new Date().toLocaleDateString()}`,
          content: noteState.content,
          course_id: courseId,
          exercise_id: exerciseId,
          chapter_id: chapterId,
          section_id: sectionId,
          subsection_index: subsectionIndex,
          knowledge_points: knowledgePoints,
          source,
          tags: noteState.selectedTags,
        }
        savedNote = await createNote(token, noteData)
      }

      onSave?.(savedNote)
      onClose?.()
    } catch (error) {
      console.error('[笔记] 保存失败:', error)
    } finally {
      setIsSaving(false)
    }
  }, [
    note,
    noteState.title,
    noteState.content,
    noteState.selectedTags,
    exerciseId,
    chapterId,
    sectionId,
    courseId,
    subsectionIndex,
    knowledgePoints,
    source,
    lang,
    onSave,
    onClose,
  ])

  const handleCreateTag = useCallback(async () => {
    if (!tagUi.newTagName.trim()) return

    const token = getStoredToken()
    if (!token) return

    try {
      const tag = await createNoteTag(token, {
        name: tagUi.newTagName.trim(),
        color: `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`,
      })
      setAvailableTags((prev) => [...prev, tag])
      setNoteState((prev) => ({ ...prev, selectedTags: [...prev.selectedTags, tag.name] }))
      setTagUi((prev) => ({ ...prev, newTagName: '' }))
    } catch (error) {
      console.error('[标签] 创建失败:', error)
    }
  }, [tagUi.newTagName])

  const toggleTag = useCallback((tagName: string) => {
    setNoteState((prev) => ({
      ...prev,
      selectedTags: prev.selectedTags.includes(tagName)
        ? prev.selectedTags.filter((t) => t !== tagName)
        : [...prev.selectedTags, tagName],
    }))
  }, [])

  const handleTitleChange = useCallback((value: string) => {
    setNoteState((prev) => ({ ...prev, title: value }))
  }, [])

  const handleContentChange = useCallback((value: string) => {
    setNoteState((prev) => ({ ...prev, content: value }))
  }, [])

  const handleNewTagNameChange = useCallback((value: string) => {
    setTagUi((prev) => ({ ...prev, newTagName: value }))
  }, [])

  const handleToggleTagSelector = useCallback(() => {
    setTagUi((prev) => ({ ...prev, showTagSelector: !prev.showTagSelector }))
  }, [])

  const commonProps = {
    note,
    title,
    content,
    selectedTags,
    selectedTagSet,
    availableTags,
    newTagName,
    showTagSelector,
    isSaving,
    lang,
    onTitleChange: handleTitleChange,
    onContentChange: handleContentChange,
    onNewTagNameChange: handleNewTagNameChange,
    onCreateTag: handleCreateTag,
    onToggleTag: toggleTag,
    onToggleTagSelector: handleToggleTagSelector,
    onSave: handleSave,
    onClose,
  }

  if (isFullPage) {
    return <NoteEditorFullPage {...commonProps} />
  }

  return <NoteEditorModal {...commonProps} />
}
