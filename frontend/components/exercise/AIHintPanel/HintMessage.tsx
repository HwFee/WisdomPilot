'use client'

import { Lightbulb, Sparkles, BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'

// ========================================
// Hint Configuration (shared across bubble + history)
// ========================================

export type HintLevel = 'light' | 'medium' | 'deep'

export const HINT_CONFIG = {
  light: {
    icon: Lightbulb,
    label: '轻度提示',
    description: '思路方向',
    cost: 1,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    hoverColor: 'hover:bg-yellow-500/20',
  },
  medium: {
    icon: Sparkles,
    label: '中度提示',
    description: '关键步骤',
    cost: 3,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    hoverColor: 'hover:bg-purple-500/20',
  },
  deep: {
    icon: BookOpen,
    label: '深度解析',
    description: '完整解答',
    cost: 5,
    color: 'text-blue-600',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    hoverColor: 'hover:bg-blue-500/20',
  },
} as const

// ========================================
// Markdown renderers (shared between bubble + legacy modal)
// ========================================

// Using a permissive type to match react-markdown's loose component shape.
// The original file used inline components with implicit types; keeping that style.
const markdownComponents = {
  h1: ({ children }: { children: React.ReactNode }) => (
    <h1 className="text-xl font-semibold text-foreground mb-2 mt-4">{children}</h1>
  ),
  h2: ({ children }: { children: React.ReactNode }) => (
    <h2 className="text-lg font-semibold text-foreground mt-3 mb-2">{children}</h2>
  ),
  h3: ({ children }: { children: React.ReactNode }) => (
    <h3 className="text-base font-medium text-foreground mt-2 mb-1">{children}</h3>
  ),
  p: ({ children }: { children: React.ReactNode }) => (
    <p className="mb-2 last:mb-0 text-muted-foreground">{children}</p>
  ),
  ul: ({ children }: { children: React.ReactNode }) => (
    <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>
  ),
  ol: ({ children }: { children: React.ReactNode }) => (
    <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>
  ),
  li: ({ children }: { children: React.ReactNode }) => (
    <li className="text-muted-foreground">{children}</li>
  ),
  blockquote: ({ children }: { children: React.ReactNode }) => (
    <blockquote className="border-l-2 border-primary/30 pl-4 italic my-2 text-muted-foreground">
      {children}
    </blockquote>
  ),
  strong: ({ children }: { children: React.ReactNode }) => (
    <strong className="font-semibold text-foreground">{children}</strong>
  ),
  code({ className, children, ...props }: { className?: string; children?: React.ReactNode }) {
    const isInline = !className
    if (isInline) {
      return (
        <code className="bg-muted text-foreground px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
          {children}
        </code>
      )
    }
    return (
      <code className={className} {...props}>
        {children}
      </code>
    )
  },
  pre({ children }: { children: React.ReactNode }) {
    return (
      <pre
        className="rounded-lg p-4 font-mono text-sm overflow-x-auto my-3"
        style={{ backgroundColor: '#1e293b', color: '#e2e8f0', border: '1px solid #334155' }}
      >
        {children}
      </pre>
    )
  },
  table: ({ children }: { children: React.ReactNode }) => (
    <div className="overflow-x-auto my-3">
      <table className="min-w-full border-collapse border border-border">{children}</table>
    </div>
  ),
  thead: ({ children }: { children: React.ReactNode }) => (
    <thead className="bg-muted">{children}</thead>
  ),
  th: ({ children }: { children: React.ReactNode }) => (
    <th className="px-3 py-2 text-left text-sm font-semibold text-foreground border border-border">
      {children}
    </th>
  ),
  td: ({ children }: { children: React.ReactNode }) => (
    <td className="px-3 py-2 text-sm text-muted-foreground border border-border">{children}</td>
  ),
} as Record<string, any>

interface HintMessageProps {
  content: string
  emptyState?: React.ReactNode
}

/**
 * HintMessage - renders the markdown hint body.
 * Used by both the streaming modal and the legacy non-streaming modal.
 */
export function HintMessage({ content, emptyState }: HintMessageProps) {
  if (!content) {
    return <>{emptyState}</>
  }

  return (
    <div className="text-muted-foreground leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex, rehypeHighlight]}
        components={markdownComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
