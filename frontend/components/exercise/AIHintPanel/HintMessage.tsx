'use client'

import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'

// ========================================
// Markdown renderers (shared between bubble + legacy modal)
// ========================================

// Using a permissive type to match react-markdown's loose component shape.
// The original file used inline components with implicit types; keeping that style.
type MarkdownChildrenProps = {
  children?: React.ReactNode
}

const markdownComponents: Components = {
  h1: ({ children }: MarkdownChildrenProps) => (
    <h1 className="text-xl font-semibold text-foreground mb-2 mt-4">{children}</h1>
  ),
  h2: ({ children }: MarkdownChildrenProps) => (
    <h2 className="text-lg font-semibold text-foreground mt-3 mb-2">{children}</h2>
  ),
  h3: ({ children }: MarkdownChildrenProps) => (
    <h3 className="text-base font-medium text-foreground mt-2 mb-1">{children}</h3>
  ),
  p: ({ children }: MarkdownChildrenProps) => (
    <p className="mb-2 last:mb-0 text-muted-foreground">{children}</p>
  ),
  ul: ({ children }: MarkdownChildrenProps) => (
    <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>
  ),
  ol: ({ children }: MarkdownChildrenProps) => (
    <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>
  ),
  li: ({ children }: MarkdownChildrenProps) => (
    <li className="text-muted-foreground">{children}</li>
  ),
  blockquote: ({ children }: MarkdownChildrenProps) => (
    <blockquote className="border-l-2 border-primary/30 pl-4 italic my-2 text-muted-foreground">
      {children}
    </blockquote>
  ),
  strong: ({ children }: MarkdownChildrenProps) => (
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
  pre({ children }: MarkdownChildrenProps) {
    return (
      <pre
        className="rounded-lg p-4 font-mono text-sm overflow-x-auto my-3"
        style={{ backgroundColor: '#1e293b', color: '#e2e8f0', border: '1px solid #334155' }}
      >
        {children}
      </pre>
    )
  },
  table: ({ children }: MarkdownChildrenProps) => (
    <div className="overflow-x-auto my-3">
      <table className="min-w-full border-collapse border border-border">{children}</table>
    </div>
  ),
  thead: ({ children }: MarkdownChildrenProps) => (
    <thead className="bg-muted">{children}</thead>
  ),
  th: ({ children }: MarkdownChildrenProps) => (
    <th className="px-3 py-2 text-left text-sm font-semibold text-foreground border border-border">
      {children}
    </th>
  ),
  td: ({ children }: MarkdownChildrenProps) => (
    <td className="px-3 py-2 text-sm text-muted-foreground border border-border">{children}</td>
  ),
}

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
