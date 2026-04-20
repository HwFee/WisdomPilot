'use client'

import { useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { FileText, Edit, Trash2, Download, Calendar, Tag } from 'lucide-react'
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
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleted, setDeleted] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleDelete = useCallback(async () => {
    if (deleted || isDeleting) return

    if (!confirm(t('确定要删除这条笔记吗？', 'Are you sure you want to delete this note?'))) {
      return
    }

    const token = getStoredToken()
    if (!token) return

    console.log('[笔记] 准备删除笔记:', { noteId: note.id, title: note.title })
    setIsDeleting(true)
    try {
      await deleteNote(token, note.id)
      console.log('[笔记] 删除成功:', note.id)
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

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString(lang === 'zh' ? 'zh-CN' : 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const sourceLabel = {
    manual: t('手动', 'Manual'),
    ai_answer: t('AI回答', 'AI Answer'),
    question: t('题目', 'Question'),
  }

  return (
    <>
      <div className="bg-card rounded-2xl border p-6 hover:shadow-lg transition-all">
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
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setShowPreview(true)}
              className="flex items-center gap-1.5 px-3 py-2 text-sm hover:bg-muted rounded-lg transition-colors"
              title={t('预览', 'Preview')}
            >
              <FileText className="w-4 h-4" />
              <span>{t('预览', 'Preview')}</span>
            </button>
            <button
              onClick={() => onEdit?.(note)}
              className="flex items-center gap-1.5 px-3 py-2 text-sm hover:bg-muted rounded-lg transition-colors"
              title={t('编辑', 'Edit')}
            >
              <Edit className="w-4 h-4" />
              <span>{t('编辑', 'Edit')}</span>
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-1.5 px-3 py-2 text-sm hover:bg-muted rounded-lg transition-colors"
              title={t('导出', 'Export')}
            >
              <Download className="w-4 h-4" />
              <span>{t('导出', 'Export')}</span>
            </button>
            <button
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

        {/* Content preview */}
        <div className="text-base text-muted-foreground leading-relaxed mb-4 line-clamp-4">
          {note.content.slice(0, 300)}
          {note.content.length > 300 && '...'}
        </div>

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
              <h2 className="font-semibold">{note.title || t('笔记预览', 'Note Preview')}</h2>
              <button
                onClick={() => setShowPreview(false)}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                {note.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
