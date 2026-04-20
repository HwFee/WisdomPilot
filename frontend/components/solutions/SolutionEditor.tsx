'use client'

import { useState } from 'react'
import { X, Eye, Edit3, Save, Megaphone } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import 'katex/dist/katex.min.css'
import type { SolutionCreate, SolutionUpdate } from '@/lib/api/solutions'

interface SolutionEditorProps {
  initialTitle?: string
  initialContent?: string
  initialIsAnnouncement?: boolean
  onSave: (data: SolutionCreate | SolutionUpdate) => Promise<void>
  onCancel: () => void
  isAdmin?: boolean
  lang?: 'zh' | 'en'
  isFullPage?: boolean
}

export function SolutionEditor({
  initialTitle = '',
  initialContent = '',
  initialIsAnnouncement = false,
  onSave,
  onCancel,
  isAdmin = false,
  lang = 'zh',
  isFullPage = false,
}: SolutionEditorProps) {
  const [title, setTitle] = useState(initialTitle)
  const [content, setContent] = useState(initialContent)
  const [isAnnouncement, setIsAnnouncement] = useState(initialIsAnnouncement)
  const [isSaving, setIsSaving] = useState(false)

  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  const handleSave = async () => {
    if (!title.trim()) return

    setIsSaving(true)
    try {
      await onSave({
        title: title.trim(),
        content: content.trim(),
        is_announcement: isAnnouncement,
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Full page mode - no modal, no fixed overlay
  if (isFullPage) {
    return (
      <div className="bg-card rounded-2xl border border-border overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
        {/* Announcement toggle - admin only */}
        {isAdmin && (
          <div className="px-6 py-4 border-b bg-muted/30">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isAnnouncement}
                onChange={e => setIsAnnouncement(e.target.checked)}
                className="w-5 h-5 rounded border-amber-400 text-amber-500 focus:ring-amber-500"
              />
              <Megaphone className="w-5 h-5 text-amber-500" />
              <span className="text-sm font-medium">{t('发布为公告', 'Post as Announcement')}</span>
            </label>
          </div>
        )}

        {/* Title input */}
        <div className="px-6 py-4 border-b">
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder={t('输入题解标题...', 'Enter solution title...')}
            className="w-full px-4 py-3 text-xl font-medium border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
            maxLength={200}
          />
        </div>

        {/* Split pane editor */}
        <div className="flex h-[calc(100%-140px)]">
          {/* Left: Editor */}
          <div className="flex-1 flex flex-col min-w-0 border-r border-border">
            <div className="flex items-center gap-2 px-6 py-3 bg-muted/50 text-sm text-muted-foreground border-b border-border">
              <Edit3 className="w-4 h-4" />
              <span>{t('Markdown 编辑器', 'Markdown Editor')}</span>
            </div>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder={t('使用 Markdown 编写，支持数学公式和代码高亮...', 'Write in Markdown with math and code support...')}
              className="flex-1 w-full p-6 resize-none bg-background font-mono text-base leading-relaxed focus:outline-none"
            />
          </div>

          {/* Right: Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-between px-6 py-3 bg-muted/50 text-sm text-muted-foreground border-b border-border">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4" />
                <span>{t('预览', 'Preview')}</span>
              </div>
              <button
                onClick={handleSave}
                disabled={isSaving || !title.trim()}
                className="flex items-center gap-2 px-4 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Save className="w-4 h-4" />
                {isSaving ? t('保存中...', 'Saving...') : t('保存', 'Save')}
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 bg-muted/30 prose prose-lg dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex, rehypeHighlight]}
              >
                {content || t('暂无内容', 'No content yet')}
              </ReactMarkdown>
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
            {initialTitle ? t('编辑题解', 'Edit Solution') : t('发布题解', 'New Solution')}
          </h2>
          <button onClick={onCancel} className="p-2 hover:bg-muted rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Announcement toggle - admin only */}
        {isAdmin && (
          <div className="px-5 py-3 border-b bg-muted/30">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isAnnouncement}
                onChange={e => setIsAnnouncement(e.target.checked)}
                className="w-4 h-4 rounded border-amber-400 text-amber-500 focus:ring-amber-500"
              />
              <Megaphone className="w-4 h-4 text-amber-500" />
              <span className="text-sm">{t('发布为公告', 'Post as Announcement')}</span>
            </label>
          </div>
        )}

        {/* Title input */}
        <div className="px-5 py-4 border-b">
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder={t('输入题解标题...', 'Enter solution title...')}
            className="w-full px-4 py-3 text-xl font-medium border-2 rounded-xl bg-background focus:border-primary focus:outline-none transition-colors"
            maxLength={200}
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
              onChange={e => setContent(e.target.value)}
              placeholder={t('使用 Markdown 编写，支持数学公式和代码高亮...', 'Write in Markdown with math and code support...')}
              className="flex-1 w-full p-4 resize-none rounded-xl border border-border bg-muted/30 font-mono text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Right: Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
              <Eye className="w-4 h-4" />
              <span>{t('预览', 'Preview')}</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 rounded-xl border border-border bg-muted/30 prose prose-lg dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex, rehypeHighlight]}
              >
                {content || t('暂无内容', 'No content yet')}
              </ReactMarkdown>
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
              onClick={onCancel}
              className="px-5 py-2.5 text-sm border-2 rounded-xl hover:bg-muted transition-colors"
            >
              {t('取消', 'Cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !title.trim()}
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