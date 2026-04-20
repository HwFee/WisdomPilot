'use client'

import { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github-dark.css'
import { X, Save, Eye, Edit3, Tags } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { createNote, updateNote, createNoteTag, getNoteTags } from '@/lib/api/notes'
import type { NoteCreate, NoteResponse, NoteTagResponse } from '@/types/api'

interface NoteEditorProps {
  note?: NoteResponse | null
  exerciseId?: number
  chapterId?: number
  subsectionIndex?: number
  knowledgePoints?: string[]
  prefillContent?: string
  prefillTitle?: string
  initialTitle?: string
  initialContent?: string
  source?: 'manual' | 'ai_answer' | 'question'
  onSave?: (note: NoteResponse) => void
  onClose?: () => void
  lang?: 'zh' | 'en'
  isFullPage?: boolean
}

export function NoteEditor({
  note,
  exerciseId,
  chapterId,
  subsectionIndex = 0,
  knowledgePoints = [],
  prefillContent,
  prefillTitle,
  initialTitle,
  initialContent,
  source = 'manual',
  onSave,
  onClose,
  lang = 'zh',
  isFullPage = false,
}: NoteEditorProps) {
  const [title, setTitle] = useState(note?.title || prefillTitle || initialTitle || '')
  const [content, setContent] = useState(note?.content || prefillContent || initialContent || '')
  const [selectedTags, setSelectedTags] = useState<string[]>(note?.tags || [])
  const [availableTags, setAvailableTags] = useState<NoteTagResponse[]>([])
  const [newTagName, setNewTagName] = useState('')
  const [showTagSelector, setShowTagSelector] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

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
          title: title || undefined,
          content,
          tags: selectedTags,
          knowledge_points: knowledgePoints,
        })
      } else {
        // Create new note
        const noteData: NoteCreate = {
          title: title || `${t('笔记', 'Note')} ${new Date().toLocaleDateString()}`,
          content,
          exercise_id: exerciseId,
          chapter_id: chapterId,
          subsection_index: subsectionIndex,
          knowledge_points: knowledgePoints,
          source,
          tags: selectedTags,
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
  }, [note, title, content, selectedTags, exerciseId, chapterId, subsectionIndex, knowledgePoints, source, t, onSave, onClose])

  const handleCreateTag = useCallback(async () => {
    if (!newTagName.trim()) return

    const token = getStoredToken()
    if (!token) return

    try {
      const tag = await createNoteTag(token, {
        name: newTagName.trim(),
        color: `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`,
      })
      setAvailableTags((prev) => [...prev, tag])
      setSelectedTags((prev) => [...prev, tag.name])
      setNewTagName('')
    } catch (error) {
      console.error('[标签] 创建失败:', error)
    }
  }, [newTagName])

  const toggleTag = useCallback((tagName: string) => {
    setSelectedTags((prev) =>
      prev.includes(tagName)
        ? prev.filter((t) => t !== tagName)
        : [...prev, tagName]
    )
  }, [])

  // Full page mode
  if (isFullPage) {
    return (
      <div className="bg-card rounded-2xl border border-border overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
        {/* Tags selector */}
        {showTagSelector && (
          <div className="px-6 py-4 border-b bg-muted/30">
            <div className="flex flex-wrap gap-2 mb-4">
              {selectedTags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-full flex items-center gap-2"
                >
                  {tag}
                  <button
                    onClick={() => toggleTag(tag)}
                    className="hover:text-primary/70"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-3 mb-4">
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateTag()}
                placeholder={t('输入新标签名', 'New tag name')}
                className="flex-1 px-4 py-2 text-sm border rounded-lg bg-background"
              />
              <button
                onClick={handleCreateTag}
                className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              >
                {t('创建', 'Create')}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {availableTags
                .filter((tag) => !selectedTags.includes(tag.name))
                .map((tag) => (
                  <button
                    key={tag.id}
                    onClick={() => toggleTag(tag.name)}
                    className="px-3 py-1.5 text-sm border-2 rounded-full hover:bg-muted transition-colors"
                    style={{ borderColor: tag.color }}
                  >
                    {tag.name}
                  </button>
                ))}
            </div>
          </div>
        )}

        {/* Title input */}
        <div className="px-6 py-4 border-b">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t('笔记标题（可选）', 'Note title (optional)')}
            className="w-full px-4 py-3 text-xl font-medium border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
          />
        </div>

        {/* Split pane editor */}
        <div className="flex h-[calc(100%-140px)]">
          {/* Left: Editor */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-center px-6 py-3 bg-muted/50 text-sm text-muted-foreground border-b border-border">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowTagSelector(!showTagSelector)}
                  className="flex items-center gap-2 px-2 py-1 hover:bg-muted rounded transition-colors"
                  title={t('管理标签', 'Manage Tags')}
                >
                  <Tags className="w-4 h-4" />
                  <span>{t('标签', 'Tags')}</span>
                </button>
              </div>
              <div className="flex items-center gap-2">
                <Edit3 className="w-4 h-4" />
                <span>{t('Markdown 编辑器', 'Markdown Editor')}</span>
              </div>
            </div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={t('使用 Markdown 编写笔记，支持数学公式和代码高亮...', 'Write your note in Markdown with math and code support...')}
              className="flex-1 w-full p-6 resize-none bg-background font-mono text-base leading-relaxed focus:outline-none"
            />
          </div>

          {/* Divider */}
          <div className="w-px bg-border" />

          {/* Right: Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-center px-6 py-3 bg-muted/50 text-sm text-muted-foreground border-b border-border">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4" />
                <span>{t('预览', 'Preview')}</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-6 bg-muted/30">
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex, rehypeHighlight]}>
                  {content}
                </ReactMarkdown>
              </div>
            </div>
            {/* Save button in preview footer */}
            <div className="px-6 py-3 border-t border-border bg-muted/30">
              <button
                onClick={handleSave}
                disabled={isSaving || !content.trim()}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Save className="w-4 h-4" />
                {isSaving ? t('保存中...', 'Saving...') : t('保存', 'Save')}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Modal mode (original)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-card rounded-2xl shadow-2xl w-full max-w-6xl max-h-[95vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-xl font-semibold">
            {note ? t('编辑笔记', 'Edit Note') : t('新建笔记', 'New Note')}
          </h2>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowTagSelector(!showTagSelector)}
              className="flex items-center gap-2 px-3 py-2 hover:bg-muted rounded-lg transition-colors"
              title={t('管理标签', 'Manage Tags')}
            >
              <Tags className="w-5 h-5" />
              <span className="text-sm">{t('标签', 'Tags')}</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tags selector */}
        {showTagSelector && (
          <div className="px-5 py-4 border-b bg-muted/30">
            <div className="flex flex-wrap gap-2 mb-4">
              {selectedTags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-full flex items-center gap-2"
                >
                  {tag}
                  <button
                    onClick={() => toggleTag(tag)}
                    className="hover:text-primary/70"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-3 mb-4">
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateTag()}
                placeholder={t('输入新标签名', 'New tag name')}
                className="flex-1 px-4 py-2 text-sm border rounded-lg bg-background"
              />
              <button
                onClick={handleCreateTag}
                className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              >
                {t('创建', 'Create')}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {availableTags
                .filter((tag) => !selectedTags.includes(tag.name))
                .map((tag) => (
                  <button
                    key={tag.id}
                    onClick={() => toggleTag(tag.name)}
                    className="px-3 py-1.5 text-sm border-2 rounded-full hover:bg-muted transition-colors"
                    style={{ borderColor: tag.color }}
                  >
                    {tag.name}
                  </button>
                ))}
            </div>
          </div>
        )}

        {/* Title input */}
        <div className="px-5 py-4 border-b">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t('笔记标题（可选）', 'Note title (optional)')}
            className="w-full px-4 py-3 text-xl font-medium border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
          />
        </div>

        {/* Split pane editor */}
        <div className="flex-1 flex gap-4 p-5 overflow-hidden">
          {/* Left: Editor */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
              <Edit3 className="w-4 h-4" />
              <span>{t('Markdown 编辑器', 'Markdown Editor')}</span>
            </div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={t('使用 Markdown 编写笔记，支持数学公式和代码高亮...', 'Write your note in Markdown with math and code support...')}
              className="flex-1 w-full p-4 resize-none rounded-xl border border-border bg-muted/30 font-mono text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Right: Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
              <Eye className="w-4 h-4" />
              <span>{t('预览', 'Preview')}</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 rounded-xl border border-border bg-muted/30">
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex, rehypeHighlight]}>
                  {content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-5 border-t bg-muted/30">
          <div className="text-sm text-muted-foreground">
            {t('支持 Markdown 格式，支持数学公式 $...$ 和 $$...$$，支持代码高亮', 'Supports Markdown, math formulas $...$ and $$...$$, code highlighting')}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-5 py-2.5 text-sm border-2 rounded-xl hover:bg-muted transition-colors"
            >
              {t('取消', 'Cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !content.trim()}
              className="px-5 py-2.5 text-sm bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {isSaving ? t('保存中...', 'Saving...') : t('保存', 'Save')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}