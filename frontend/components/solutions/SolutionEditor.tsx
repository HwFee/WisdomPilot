'use client'

import { useState } from 'react'
import { X, Eye, Edit3, Save, Megaphone, ArrowLeft, Type } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { MarkdownRenderer } from '@/components/editor/MarkdownRenderer'
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
  const [title, setTitle] = useState(() => initialTitle)
  const [content, setContent] = useState(() => initialContent)
  const [isAnnouncement, setIsAnnouncement] = useState(() => initialIsAnnouncement)
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
      <div className="bg-card border border-border flex flex-col overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
        {/* Header */}
        <header className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-3 min-w-0">
            <Button variant="ghost" size="icon" onClick={onCancel} aria-label={t('返回', 'Back')} className="shrink-0">
              <ArrowLeft className="size-5" strokeWidth={1.5} />
            </Button>
            <h2 className="text-base font-semibold uppercase tracking-[1.5px] truncate">
              {initialTitle ? t('编辑题解', 'Edit Solution') : t('发布题解', 'New Solution')}
            </h2>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <Button type="button" variant="outline" size="sm" onClick={onCancel} disabled={isSaving}>
              <X className="size-4 mr-1.5" strokeWidth={1.5} />
              {t('取消', 'Cancel')}
            </Button>
            <Button type="button" size="sm" onClick={handleSave} disabled={isSaving || !title.trim()} className="gap-2">
              <Save className="size-4" strokeWidth={1.5} />
              {isSaving ? t('保存中...', 'Saving...') : t('发布题解', 'Post Solution')}
            </Button>
          </div>
        </header>

        {/* Announcement toggle - admin only */}
        {isAdmin && (
          <div className="px-6 py-3 border-b border-border bg-muted/20">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isAnnouncement}
                onChange={e => setIsAnnouncement(e.target.checked)}
                className="size-4 border-border"
              />
              <Megaphone className="size-4 text-amber-500" strokeWidth={1.5} />
              <span className="text-sm font-medium">{t('发布为公告', 'Post as Announcement')}</span>
            </label>
          </div>
        )}

        {/* Title input */}
        <div className="border-b border-border px-6 py-4">
          <div className="flex items-center gap-3">
            <Type className="size-5 text-muted-foreground shrink-0" strokeWidth={1.5} />
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder={t('输入题解标题...', 'Enter solution title...')}
              aria-label={t('题解标题', 'Solution title')}
              className="flex-1 bg-transparent text-xl font-semibold text-foreground placeholder:text-muted-foreground py-1 focus:outline-none"
              maxLength={200}
            />
          </div>
        </div>

        {/* Split pane editor */}
        <div className="flex-1 flex min-h-0">
          {/* Left: Editor */}
          <div className="flex-1 flex flex-col min-w-0 border-r border-border">
            <div className="flex items-center justify-between px-4 py-2 text-xs font-medium uppercase tracking-[1.5px] text-muted-foreground border-b border-border bg-muted/20">
              <div className="flex items-center gap-2">
                <Edit3 className="size-3.5" strokeWidth={1.5} />
                <span>{t('编辑', 'Edit')}</span>
              </div>
              <span className="text-[10px] normal-case tracking-normal">Markdown</span>
            </div>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder={t('开始编写题解内容...', 'Start writing solution content...')}
              aria-label={t('题解内容', 'Solution content')}
              className="flex-1 w-full p-6 resize-none bg-transparent font-mono text-base leading-relaxed focus:outline-none"
            />
          </div>

          {/* Right: Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-between px-4 py-2 text-xs font-medium uppercase tracking-[1.5px] text-muted-foreground border-b border-border bg-muted/20">
              <div className="flex items-center gap-2">
                <Eye className="size-3.5" strokeWidth={1.5} />
                <span>{t('预览', 'Preview')}</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="markdown-body">
                {content ? <MarkdownRenderer content={content} /> : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Modal mode (original)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-card border border-border w-full max-w-6xl max-h-[95vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-6 border-b">
          <h2 className="text-[13px] font-semibold uppercase tracking-[1.5px]">
            {initialTitle ? t('编辑题解', 'Edit Solution') : t('发布题解', 'New Solution')}
          </h2>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onCancel}
            aria-label={t('关闭', 'Close')}
          >
            <X className="size-5" strokeWidth={1.5} />
          </Button>
        </div>

        {/* Announcement toggle - admin only */}
        {isAdmin && (
          <div className="px-5 py-3 border-b bg-muted/30">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isAnnouncement}
                onChange={e => setIsAnnouncement(e.target.checked)}
                className="size-4 border-border"
              />
              <Megaphone className="size-4" strokeWidth={1.5} />
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
            aria-label={t('题解标题', 'Solution title')}
            className="w-full h-12 px-3 bg-background border border-border text-xl font-medium focus:outline-none focus:border-foreground"
            maxLength={200}
          />
        </div>

        {/* Split pane editor */}
        <div className="flex-1 flex gap-4 p-5 overflow-hidden">
          {/* Left: Editor */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-center mb-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Edit3 className="size-4" />
                <span>{t('Markdown 编辑器', 'Markdown Editor')}</span>
              </div>
            </div>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder={t('使用 Markdown 编写，支持数学公式和代码高亮...', 'Write in Markdown with math and code support...')}
              aria-label={t('题解内容', 'Solution content')}
              className="flex-1 w-full p-4 resize-none rounded-xl border border-border bg-muted/30 font-mono text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Right: Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-center mb-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Eye className="size-4" />
                <span>{t('预览', 'Preview')}</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 rounded-xl border border-border bg-muted/30">
              <div className="markdown-body">
                <MarkdownRenderer content={content} />
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
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
            >
              {t('取消', 'Cancel')}
            </Button>
            <Button
              type="button"
              onClick={handleSave}
              disabled={isSaving || !title.trim()}
            >
              <Save className="size-4 mr-2" strokeWidth={1.5} />
              {isSaving ? t('保存中...', 'Saving...') : t('保存', 'Save')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
