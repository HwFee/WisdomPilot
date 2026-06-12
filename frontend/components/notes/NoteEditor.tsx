'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github-dark.css'
import { X, Save, Eye, Edit3, Tags, Minimize2 } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { createNote, updateNote, createNoteTag, getNoteTags } from '@/lib/api/notes'
import type { NoteCreate, NoteResponse, NoteTagResponse } from '@/types/api'

function translate(lang: 'zh' | 'en', zh: string, en: string) {
  return lang === 'zh' ? zh : en
}

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
    selectedTags: note?.tags || [] as string[],
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
  }, [note, noteState.title, noteState.content, noteState.selectedTags, exerciseId, chapterId, sectionId, courseId, subsectionIndex, knowledgePoints, source, lang, onSave, onClose])

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
      setNoteState(prev => ({ ...prev, selectedTags: [...prev.selectedTags, tag.name] }))
      setTagUi(prev => ({ ...prev, newTagName: '' }))
    } catch (error) {
      console.error('[标签] 创建失败:', error)
    }
  }, [tagUi.newTagName])

  const toggleTag = useCallback((tagName: string) => {
    setNoteState(prev => ({
      ...prev,
      selectedTags: prev.selectedTags.includes(tagName)
        ? prev.selectedTags.filter((t) => t !== tagName)
        : [...prev.selectedTags, tagName],
    }))
  }, [])

  // ========== 完整页面模式（分屏预览）==========
  if (isFullPage) {
    return (
      <div className="bg-card rounded-2xl border border-border overflow-hidden h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-muted/30">
          <h2 className="text-lg font-semibold">
            {note ? translate(lang, '编辑笔记', 'Edit Note') : translate(lang, '新建笔记', 'New Note')}
          </h2>
          <div className="flex items-center gap-3">
            <button type="button"
              onClick={() => setTagUi(prev => ({ ...prev, showTagSelector: !prev.showTagSelector }))}
              className="flex items-center gap-2 px-3 py-2 hover:bg-muted rounded-lg transition-colors text-sm"
              title={translate(lang, '管理标签', 'Manage Tags')}
            >
              <Tags className="size-4" />
              <span>{translate(lang, '标签', 'Tags')}</span>
            </button>
            {onClose && (
              <button type="button"
                onClick={onClose}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
                title={translate(lang, '关闭', 'Close')}
              >
                <Minimize2 className="size-5" />
              </button>
            )}
          </div>
        </div>

        {/* Tags selector */}
        {tagUi.showTagSelector && (
          <div className="px-6 py-4 border-b bg-muted/30">
            <div className="flex flex-wrap gap-2 mb-4">
              {noteState.selectedTags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-full flex items-center gap-2"
                >
                  {tag}
                  <button type="button"
                    onClick={() => toggleTag(tag)}
                    className="hover:text-primary/70"
                  >
                    <X className="size-3.5" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-3 mb-4">
              <input
                type="text"
                value={tagUi.newTagName}
                onChange={(e) => setTagUi(prev => ({ ...prev, newTagName: e.target.value }))}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateTag()}
                placeholder={translate(lang, '输入新标签名', 'New tag name')}
                aria-label={translate(lang, '新标签名', 'New tag name')}
                className="flex-1 px-4 py-2 text-sm border rounded-lg bg-background"
              />
              <button type="button"
                onClick={handleCreateTag}
                className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              >
                {translate(lang, '创建', 'Create')}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {availableTags.flatMap((tag) =>
                selectedTagSet.has(tag.name)
                  ? []
                  : [
                      <button type="button"
                        key={tag.id}
                        onClick={() => toggleTag(tag.name)}
                        className="px-3 py-1.5 text-sm border-2 rounded-full hover:bg-muted transition-colors"
                        style={{ borderColor: tag.color }}
                      >
                        {tag.name}
                      </button>,
                    ]
              )}
            </div>
          </div>
        )}

        {/* Title input */}
        <div className="px-6 py-4 border-b">
          <input
            type="text"
            value={noteState.title}
            onChange={(e) => setNoteState(prev => ({ ...prev, title: e.target.value }))}
            placeholder={translate(lang, '笔记标题（可选）', 'Note title (optional)')}
            aria-label={translate(lang, '笔记标题', 'Note title')}
            className="w-full px-4 py-3 text-xl font-medium border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
          />
        </div>

        {/* Split pane editor */}
        <div className="flex-1 flex min-h-0">
          {/* Left: Editor */}
          <div className="flex-1 flex flex-col min-w-0 border-r">
            <div className="flex items-center justify-center px-6 py-3 bg-muted/50 text-sm text-muted-foreground border-b border-border">
              <div className="flex items-center gap-2">
                <Edit3 className="size-4" />
                <span>{translate(lang, 'Markdown 编辑器', 'Markdown Editor')}</span>
              </div>
            </div>
            <textarea
              value={noteState.content}
              onChange={(e) => setNoteState(prev => ({ ...prev, content: e.target.value }))}
              placeholder={translate(lang, '使用 Markdown 编写，支持数学公式和代码高亮...', 'Write in Markdown with math and code support...')}
              aria-label={translate(lang, '笔记内容', 'Note content')}
              className="flex-1 w-full p-6 resize-none bg-background font-mono text-base leading-relaxed focus:outline-none"
            />
          </div>

          {/* Right: Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-center px-6 py-3 bg-muted/50 text-sm text-muted-foreground border-b border-border">
              <div className="flex items-center gap-2">
                <Eye className="size-4" />
                <span>{translate(lang, '实时预览', 'Live Preview')}</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-6 bg-muted/30">
              <div className="prose prose-lg dark:prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex, rehypeHighlight]}
                  components={{
                    h1: ({ children }) => <h1 className="text-3xl font-semibold mt-6 mb-3">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-2xl font-semibold mt-5 mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-xl font-semibold mt-4 mb-2">{children}</h3>,
                    h4: ({ children }) => <h4 className="text-lg font-semibold mt-3 mb-1">{children}</h4>,
                    h5: ({ children }) => <h5 className="text-base font-semibold mt-2 mb-1">{children}</h5>,
                    h6: ({ children }) => <h6 className="text-sm font-semibold mt-2 mb-1 text-muted-foreground">{children}</h6>,
                    p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
                    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                    blockquote: ({ children }) => <blockquote className="border-l-2 border-primary pl-4 my-3 italic text-muted-foreground">{children}</blockquote>,
                    code: ({ className, children, ...props }) => {
                      const isInline = !className
                      return isInline
                        ? <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>{children}</code>
                        : <code className={className} {...props}>{children}</code>
                    },
                    pre: ({ children }) => <pre className="bg-muted p-4 rounded-lg overflow-x-auto my-3">{children}</pre>,
                    a: ({ href, children }) => <a href={href} className="text-primary underline hover:text-primary/80">{children}</a>,
                    table: ({ children }) => <table className="w-full border-collapse my-3">{children}</table>,
                    th: ({ children }) => <th className="border border-border px-3 py-2 bg-muted font-semibold text-left">{children}</th>,
                    td: ({ children }) => <td className="border border-border px-3 py-2">{children}</td>,
                  }}
                >
                  {content || translate(lang, '暂无内容', 'No content yet')}
                </ReactMarkdown>
              </div>
            </div>
            {/* Save button in preview footer */}
            <div className="px-6 py-3 border-t border-border bg-muted/30">
              <button type="button"
                onClick={handleSave}
                disabled={isSaving || !content.trim()}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Save className="size-4" />
                {isSaving ? translate(lang, '保存中...', 'Saving...') : translate(lang, '保存', 'Save')}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ========== 方形弹窗模式（用于做题页面）==========
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-card rounded-2xl shadow-2xl w-full max-w-4xl aspect-square max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-xl font-semibold">
            {note ? translate(lang, '编辑笔记', 'Edit Note') : translate(lang, '新建笔记', 'New Note')}
          </h2>
          <div className="flex items-center gap-3">
            <button type="button"
              onClick={() => setTagUi(prev => ({ ...prev, showTagSelector: !prev.showTagSelector }))}
              className="flex items-center gap-2 px-3 py-2 hover:bg-muted rounded-lg transition-colors"
              title={translate(lang, '管理标签', 'Manage Tags')}
            >
              <Tags className="size-5" />
              <span className="text-sm">{translate(lang, '标签', 'Tags')}</span>
            </button>
            <button type="button"
              onClick={onClose}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <X className="size-5" />
            </button>
          </div>
        </div>

        {/* Tags selector */}
        {tagUi.showTagSelector && (
          <div className="px-5 py-4 border-b bg-muted/30">
            <div className="flex flex-wrap gap-2 mb-4">
              {noteState.selectedTags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-full flex items-center gap-2"
                >
                  {tag}
                  <button type="button"
                    onClick={() => toggleTag(tag)}
                    className="hover:text-primary/70"
                  >
                    <X className="size-4" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-3 mb-4">
              <input
                type="text"
                value={tagUi.newTagName}
                onChange={(e) => setTagUi(prev => ({ ...prev, newTagName: e.target.value }))}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateTag()}
                placeholder={translate(lang, '输入新标签名', 'New tag name')}
                aria-label={translate(lang, '新标签名', 'New tag name')}
                className="flex-1 px-4 py-2 text-sm border rounded-lg bg-background"
              />
              <button type="button"
                onClick={handleCreateTag}
                className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              >
                {translate(lang, '创建', 'Create')}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {(() => {
                const nodes: React.ReactNode[] = []
                for (const tag of availableTags) {
                  if (selectedTagSet.has(tag.name)) continue
                  nodes.push(
                    <button type="button"
                      key={tag.id}
                      onClick={() => toggleTag(tag.name)}
                      className="px-3 py-1.5 text-sm border-2 rounded-full hover:bg-muted transition-colors"
                      style={{ borderColor: tag.color }}
                    >
                      {tag.name}
                    </button>
                  )
                }
                return nodes
              })()}
            </div>
          </div>
        )}

        {/* Title input */}
        <div className="px-5 py-4 border-b">
          <input
            type="text"
            value={noteState.title}
            onChange={(e) => setNoteState(prev => ({ ...prev, title: e.target.value }))}
            placeholder={translate(lang, '笔记标题（可选）', 'Note title (optional)')}
            aria-label={translate(lang, '笔记标题', 'Note title')}
            className="w-full px-4 py-3 text-xl font-medium border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
          />
        </div>

        {/* Split pane editor - 方形弹窗内也有分屏预览 */}
        <div className="flex-1 flex gap-4 p-5 overflow-hidden min-h-0">
          {/* Left: Editor */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-center mb-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Edit3 className="size-4" />
                <span>{translate(lang, '编辑', 'Edit')}</span>
              </div>
            </div>
            <textarea
              value={noteState.content}
              onChange={(e) => setNoteState(prev => ({ ...prev, content: e.target.value }))}
              placeholder={translate(lang, '使用 Markdown 编写...', 'Write in Markdown...')}
              aria-label={translate(lang, '笔记内容', 'Note content')}
              className="flex-1 w-full p-4 resize-none rounded-xl border border-border bg-muted/30 font-mono text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Right: Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-center mb-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Eye className="size-4" />
                <span>{translate(lang, '预览', 'Preview')}</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 rounded-xl border border-border bg-muted/30">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex, rehypeHighlight]}
                >
                  {content || translate(lang, '暂无内容', 'No content yet')}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-5 border-t bg-muted/30">
          <div className="text-sm text-muted-foreground">
            {translate(lang, '支持 Markdown，数学公式 $...$ 和代码高亮', 'Markdown, math $...$ and code highlighting')}
          </div>
          <div className="flex gap-3">
            <button type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-sm border-2 rounded-xl hover:bg-muted transition-colors"
            >
              {translate(lang, '取消', 'Cancel')}
            </button>
            <button type="button"
              onClick={handleSave}
              disabled={isSaving || !content.trim()}
              className="px-5 py-2.5 text-sm bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              <Save className="size-4" />
              {isSaving ? translate(lang, '保存中...', 'Saving...') : translate(lang, '保存', 'Save')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
