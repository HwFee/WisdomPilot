'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { FileText, Edit, Trash2, Download, Calendar, Tag, ExternalLink, Loader2 } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { deleteNote, exportNote } from '@/lib/api/notes'
import type { NoteResponse } from '@/types/api'

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
  const router = useRouter()
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleted, setDeleted] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  // 是否正在处理中
  const isProcessing = note.processing_status === 'pending' || note.processing_status === 'processing'

  const handleDelete = useCallback(async () => {
    if (deleted || isDeleting) return

    if (!confirm(t('确定要删除这条笔记吗？', 'Are you sure you want to delete this note?'))) {
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
      alert(t('删除失败: ' + (error instanceof Error ? error.message : '未知错误'), 'Delete failed: ' + (error instanceof Error ? error.message : 'Unknown error')))
    } finally {
      setIsDeleting(false)
    }
  }, [note.id, t, onDelete, deleted, isDeleting])

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
    // 转换为北京时间显示
    return new Intl.DateTimeFormat(lang === 'zh' ? 'zh-CN' : 'en-US', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  // 跳转到关联题目
  const handleGoToExercise = useCallback(() => {
    if (!note.exercise_id) return

    // 挑战之路笔记（无 course_id/chapter_id）
    if (!note.course_id && !note.chapter_id) {
      router.push('/arena')
      return
    }

    if (note.chapter_id && note.course_id && note.section_id) {
      // 完整参数：跳转到具体小节和题目
      router.push(`/mastery/${note.course_id}?chapter=${note.chapter_id}&section=${note.section_id}&exercise=${note.exercise_id}&skip=1`)
    } else if (note.chapter_id && note.course_id) {
      // 缺少 section_id：跳转到章节和题目
      router.push(`/mastery/${note.course_id}?chapter=${note.chapter_id}&exercise=${note.exercise_id}&skip=1`)
    } else if (note.course_id) {
      // 只有课程：跳转到精进之路
      router.push(`/mastery/${note.course_id}`)
    }
  }, [note.exercise_id, note.chapter_id, note.course_id, note.section_id, router])

  const sourceLabel = {
    manual: t('手动', 'Manual'),
    ai_answer: t('AI回答', 'AI Answer'),
    question: t('题目', 'Question'),
  }

  return (
    <>
      <div className={`bg-card rounded-2xl border p-6 hover:shadow-lg transition-all ${isProcessing ? 'opacity-80' : ''}`}>
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-foreground truncate">
              {note.title || t('无标题笔记', 'Untitled Note')}
            </h3>
            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4" />
                {formatDate(note.updated_at)}
              </span>
              <span className="px-2 py-0.5 bg-muted rounded-md text-xs font-medium">
                {sourceLabel[note.source] || note.source}
              </span>
              {/* 关联题目链接 */}
              {note.exercise_id && (
                <button type="button"
                  onClick={handleGoToExercise}
                  className="flex items-center gap-1 px-2 py-0.5 bg-primary/10 text-primary rounded-md text-xs font-medium hover:bg-primary/20 transition-colors"
                  title={t('跳转到关联题目', 'Go to related exercise')}
                >
                  <ExternalLink className="w-3 h-3" />
                  {t('题目 #', 'Exercise #')}{note.exercise_id}
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button type="button"
              onClick={() => setShowPreview(true)}
              className="flex items-center gap-1.5 px-3 py-2 text-sm hover:bg-muted rounded-lg transition-colors"
              title={t('预览', 'Preview')}
            >
              <FileText className="w-4 h-4" />
              <span>{t('预览', 'Preview')}</span>
            </button>
            <button type="button"
              onClick={() => onEdit?.(note)}
              className="flex items-center gap-1.5 px-3 py-2 text-sm hover:bg-muted rounded-lg transition-colors"
              title={t('编辑', 'Edit')}
            >
              <Edit className="w-4 h-4" />
              <span>{t('编辑', 'Edit')}</span>
            </button>
            <button type="button"
              onClick={handleExport}
              className="flex items-center gap-1.5 px-3 py-2 text-sm hover:bg-muted rounded-lg transition-colors"
              title={t('导出', 'Export')}
            >
              <Download className="w-4 h-4" />
              <span>{t('导出', 'Export')}</span>
            </button>
            <button type="button"
              onClick={handleDelete}
              disabled={isDeleting || deleted}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 rounded-lg transition-colors disabled:opacity-50"
              title={t('删除', 'Delete')}
            >
              <Trash2 className="w-4 h-4" />
              <span>{t('删除', 'Delete')}</span>
            </button>
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
            <Loader2 className="w-4 h-4 animate-spin text-amber-500" />
            <span className="text-sm text-amber-600 dark:text-amber-400">
              {t('这条笔记正在处理中...', 'This note is being processed...')}
            </span>
          </div>
        )}

        {/* Tags */}
        {note.tags && note.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {note.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full flex items-center gap-1.5"
              >
                <Tag className="w-3.5 h-3.5" />
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
                className="px-3 py-1 bg-muted text-muted-foreground text-sm rounded-full"
              >
                {kp}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-3">
                <h2 className="font-semibold">{note.title || t('笔记预览', 'Note Preview')}</h2>
                {note.exercise_id && (
                  <button type="button"
                    onClick={handleGoToExercise}
                    className="flex items-center gap-1 px-2 py-1 text-xs bg-primary/10 text-primary rounded-md hover:bg-primary/20 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    {t('跳转到题目', 'Go to exercise')}
                  </button>
                )}
                {isProcessing && (
                  <span className="flex items-center gap-1 px-2 py-1 text-xs bg-amber-500/10 text-amber-600 rounded-md">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    {t('处理中', 'Processing')}
                  </span>
                )}
              </div>
              <button type="button"
                onClick={() => setShowPreview(false)}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
              >
                ×
              </button>
            </div>
            <div className={`flex-1 overflow-y-auto p-6 prose prose-sm dark:prose-invert max-w-none ${isProcessing ? 'blur-sm' : ''}`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
              >
                {note.content}
              </ReactMarkdown>
            </div>
            {isProcessing && (
              <div className="p-4 border-t bg-amber-500/5 flex items-center justify-center gap-2 text-amber-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">{t('笔记正在处理中，请稍后刷新查看...', 'Note is being processed, please refresh later...')}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
