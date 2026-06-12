'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { FileText, Edit, Trash2, Download, Calendar, Tag, ExternalLink, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Panel, PanelHeader } from '@/components/layout'
import { getStoredToken } from '@/lib/api'
import { deleteNote, exportNote } from '@/lib/api/notes'
import type { NoteResponse } from '@/types/api'

function translate(lang: 'zh' | 'en', zh: string, en: string) {
  return lang === 'zh' ? zh : en
}

// Module-level Beijing timezone formatters
const BEIJING_ZH_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})
const BEIJING_EN_FORMATTER = new Intl.DateTimeFormat('en-US', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

interface NoteCardProps {
  note: NoteResponse
  onEdit?: (note: NoteResponse) => void
  onDelete?: (noteId: string) => void
  lang?: 'zh' | 'en'
}

export function NoteCard({
  note,
  onEdit,
  onDelete,
  lang = 'zh',
}: NoteCardProps) {
  const { push } = useRouter()
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleted, setDeleted] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  // 是否正在处理中
  const isProcessing = note.processing_status === 'pending' || note.processing_status === 'processing'

  const handleDelete = useCallback(async () => {
    if (deleted || isDeleting) return

    if (!confirm(translate(lang, '确定要删除这条笔记吗？', 'Are you sure you want to delete this note?'))) {
      return
    }

    const token = getStoredToken()
    if (!token) return

    setIsDeleting(true)
    try {
      await deleteNote(token, note.id)
      setDeleted(true)
      onDelete?.(note.id)
    } catch (error) {
      console.error('[笔记] 删除失败:', { noteId: note.id, error })
      alert(translate(lang, '删除失败: ' + (error instanceof Error ? error.message : '未知错误'), 'Delete failed: ' + (error instanceof Error ? error.message : 'Unknown error')))
    } finally {
      setIsDeleting(false)
    }
  }, [note.id, lang, onDelete, deleted, isDeleting])

  const handleExport = useCallback(async () => {
    const token = getStoredToken()
    if (!token) return

    try {
      const response = await exportNote(token, note.id)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `note_${note.id}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('[笔记] 导出失败:', error)
    }
  }, [note.id])

  // 北京时间格式化 (UTC+8)
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return (lang === 'zh' ? BEIJING_ZH_FORMATTER : BEIJING_EN_FORMATTER).format(date)
  }

  // 跳转到关联题目
  const handleGoToExercise = useCallback(() => {
    if (!note.exercise_id) return

    // 挑战之路笔记（无 course_id/chapter_id）
    if (!note.course_id && !note.chapter_id) {
      push('/arena')
      return
    }

    if (note.chapter_id && note.course_id && note.section_id) {
      // 完整参数：跳转到具体小节和题目
      push(`/mastery/${note.course_id}?chapter=${note.chapter_id}&section=${note.section_id}&exercise=${note.exercise_id}&skip=1`)
    } else if (note.chapter_id && note.course_id) {
      // 缺少 section_id：跳转到章节和题目
      push(`/mastery/${note.course_id}?chapter=${note.chapter_id}&exercise=${note.exercise_id}&skip=1`)
    } else if (note.course_id) {
      // 只有课程：跳转到精进之路
      push(`/mastery/${note.course_id}`)
    }
  }, [note.exercise_id, note.chapter_id, note.course_id, note.section_id, push])

  const sourceLabel = {
    manual: translate(lang, '手动', 'Manual'),
    ai_answer: translate(lang, 'AI回答', 'AI Answer'),
    question: translate(lang, '题目', 'Question'),
  }

  return (
    <>
      <Panel className={`p-6 hover:border-foreground/50 transition-colors ${isProcessing ? 'opacity-80' : ''}`}>
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-foreground truncate">
              {note.title || translate(lang, '无标题笔记', 'Untitled Note')}
            </h3>
            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Calendar className="size-4" />
                {formatDate(note.updated_at)}
              </span>
              <span className="px-2 py-0.5 bg-muted rounded-md text-xs font-medium">
                {sourceLabel[note.source] || note.source}
              </span>
              {/* 关联题目链接 */}
              {note.exercise_id && (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={handleGoToExercise}
                  className="h-6 px-2 gap-1"
                  title={translate(lang, '跳转到关联题目', 'Go to related exercise')}
                >
                  <ExternalLink className="size-3" />
                  {translate(lang, '题目 #', 'Exercise #')}{note.exercise_id}
                </Button>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => setShowPreview(true)}
              title={translate(lang, '预览', 'Preview')}
              aria-label={translate(lang, '预览', 'Preview')}
            >
              <FileText className="size-4" strokeWidth={1.5} />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => onEdit?.(note)}
              title={translate(lang, '编辑', 'Edit')}
              aria-label={translate(lang, '编辑', 'Edit')}
            >
              <Edit className="size-4" strokeWidth={1.5} />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleExport}
              title={translate(lang, '导出', 'Export')}
              aria-label={translate(lang, '导出', 'Export')}
            >
              <Download className="size-4" strokeWidth={1.5} />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleDelete}
              disabled={isDeleting || deleted}
              className="text-red-500 hover:text-red-600"
              title={translate(lang, '删除', 'Delete')}
              aria-label={translate(lang, '删除', 'Delete')}
            >
              <Trash2 className="size-4" strokeWidth={1.5} />
            </Button>
          </div>
        </div>

        {/* Content preview - show blur effect when processing */}
        <div className={`text-base text-muted-foreground leading-relaxed mb-4 line-clamp-4 prose prose-sm dark:prose-invert max-w-none ${isProcessing ? 'blur-sm select-none' : ''}`}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {note.content.slice(0, 500)}
          </ReactMarkdown>
        </div>

        {/* Processing indicator */}
        {isProcessing && (
          <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl mb-4">
            <Loader2 className="size-4 animate-spin text-amber-500" />
            <span className="text-sm text-amber-600 dark:text-amber-400">
              {translate(lang, '这条笔记正在处理中...', 'This note is being processed...')}
            </span>
          </div>
        )}

        {/* Tags */}
        {note.tags && note.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {note.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1.5 border border-border px-3 py-1 text-sm text-foreground"
              >
                <Tag className="size-3.5" strokeWidth={1.5} />
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Knowledge points */}
        {note.knowledge_points && note.knowledge_points.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {note.knowledge_points.map((kp) => (
              <span
                key={kp}
                className="border border-border px-3 py-1 text-sm text-muted-foreground"
              >
                {kp}
              </span>
            ))}
          </div>
        )}
      </Panel>

      {/* Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Panel className="w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
            <PanelHeader
              title={note.title || translate(lang, '笔记预览', 'Note Preview')}
              action={
                <div className="flex items-center gap-2">
                  {note.exercise_id && (
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={handleGoToExercise}
                      className="h-7 px-2 gap-1"
                    >
                      <ExternalLink className="size-3" />
                      {translate(lang, '跳转到题目', 'Go to exercise')}
                    </Button>
                  )}
                  {isProcessing && (
                    <span className="flex items-center gap-1 px-2 py-1 text-xs bg-amber-500/10 text-amber-600 rounded-md">
                      <Loader2 className="size-3 animate-spin" />
                      {translate(lang, '处理中', 'Processing')}
                    </span>
                  )}
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowPreview(false)}
                    aria-label={translate(lang, '关闭', 'Close')}
                  >
                    <X className="size-4" strokeWidth={1.5} />
                  </Button>
                </div>
              }
            />
            <div className={`flex-1 overflow-y-auto p-6 prose prose-sm dark:prose-invert max-w-none ${isProcessing ? 'blur-sm' : ''}`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
              >
                {note.content}
              </ReactMarkdown>
            </div>
            {isProcessing && (
              <div className="p-4 border-t border-border bg-amber-500/5 flex items-center justify-center gap-2 text-amber-600">
                <Loader2 className="size-4 animate-spin" />
                <span className="text-sm">{translate(lang, '笔记正在处理中，请稍后刷新查看...', 'Note is being processed, please refresh later...')}</span>
              </div>
            )}
          </Panel>
        </div>
      )}
    </>
  )
}
