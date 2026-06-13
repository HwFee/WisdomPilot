"use client"

import React, { useState, useCallback } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import rehypeHighlight from "rehype-highlight"
import "highlight.js/styles/github-dark.css"
import "katex/dist/katex.min.css"
import { FileText } from "lucide-react"
import { createNoteFromQuestion } from "@/lib/api/notes"
import { getStoredToken } from "@/lib/api"

interface KnowledgeOrbMessageBubbleProps {
  role: "user" | "ai"
  content: string
  /** Context IDs for saving as note */
  courseId?: number
  chapterId?: number
  sectionId?: number
  exerciseId?: number
  knowledgePoints?: string[]
}

const aiMarkdownComponents = {
  p: ({ children }: { children?: React.ReactNode }) => <p className="mb-1 last:mb-0 whitespace-pre-wrap">{children}</p>,
  code: ({ className, children, ...props }: React.ComponentProps<'code'>) => {
    const isInline = !className
    return isInline ? (
      <code className="bg-muted px-1.5 py-0.5 rounded text-[0.85em] text-foreground font-mono border border-border" {...props}>
        {children}
      </code>
    ) : (
      <code className={className} {...props}>{children}</code>
    )
  },
  pre: ({ children }: { children?: React.ReactNode }) => (
    <pre className="rounded-lg p-2 font-mono text-[0.85em] overflow-x-auto mb-1 last:mb-0 bg-muted text-foreground border border-border">
      {children}
    </pre>
  ),
  ul: ({ children }: { children?: React.ReactNode }) => <ul className="list-disc ml-3 mb-1 last:mb-0 space-y-0.5">{children}</ul>,
  ol: ({ children }: { children?: React.ReactNode }) => <ol className="list-decimal ml-3 mb-1 last:mb-0 space-y-0.5">{children}</ol>,
  li: ({ children }: { children?: React.ReactNode }) => <li className="leading-snug">{children}</li>,
  strong: ({ children }: { children?: React.ReactNode }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }: { children?: React.ReactNode }) => <em>{children}</em>,
}

export function KnowledgeOrbMessageBubble({
  role,
  content,
  courseId,
  chapterId,
  sectionId,
  exerciseId,
  knowledgePoints,
}: KnowledgeOrbMessageBubbleProps) {
  const isUser = role === "user"
  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSaveAsNote = useCallback(async () => {
    if (!content || isSaving || saved) return
    const token = getStoredToken()
    if (!token) return

    setIsSaving(true)
    try {
      await createNoteFromQuestion(token, {
        title: "AI 回答笔记",
        content: content,
        course_id: courseId,
        chapter_id: chapterId,
        section_id: sectionId,
        exercise_id: exerciseId,
        source: "ai_answer",
        ai_answer_content: content,
        knowledge_points: knowledgePoints || [],
      })
      setSaved(true)
    } catch (error) {
      console.error("[笔记] 保存失败:", error)
      alert("笔记保存失败，请重试")
    } finally {
      setIsSaving(false)
    }
  }, [content, isSaving, saved, courseId, chapterId, sectionId, exerciseId, knowledgePoints])

  return (
    <div className="flex flex-col gap-1">
      <div
        className={`rounded-2xl px-3 py-2 leading-relaxed text-xs max-w-[88%] ${
          isUser ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
        }`}
      >
        {isUser ? (
          <span className="whitespace-pre-wrap">{content}</span>
        ) : (
          <div className="prose prose-xs prose-slate max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex, rehypeHighlight]}
              components={aiMarkdownComponents}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
      {!isUser && (
        <button type="button"
          onClick={handleSaveAsNote}
          disabled={isSaving || saved}
          className="flex items-center gap-1 px-2 py-1 text-xs rounded-md transition-colors hover:bg-muted disabled:opacity-50 w-fit text-primary"
        >
          <FileText className="size-3" strokeWidth={1.5} />
          {saved ? "已保存" : isSaving ? "保存中..." : "记为笔记"}
        </button>
      )}
    </div>
  )
}
