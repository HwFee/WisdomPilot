"use client"

import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import "highlight.js/styles/github-dark.css"
import "katex/dist/katex.min.css"

interface KnowledgeOrbStreamingBubbleProps {
  streamingText: string
}

const streamingMarkdownComponents = {
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

export function KnowledgeOrbStreamingBubble({ streamingText }: KnowledgeOrbStreamingBubbleProps) {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl rounded-bl-sm px-3 py-2 bg-secondary text-secondary-foreground max-w-[88%] text-xs">
        {streamingText ? (
          <div className="prose prose-xs prose-slate max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
              components={streamingMarkdownComponents}
            >
              {streamingText}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex items-center gap-1 py-1">
            <span className="block size-1.5 rounded-full animate-typing-dot animate-typing-dot-0 bg-muted-foreground" />
            <span className="block size-1.5 rounded-full animate-typing-dot animate-typing-dot-1 bg-muted-foreground" />
            <span className="block size-1.5 rounded-full animate-typing-dot animate-typing-dot-2 bg-muted-foreground" />
          </div>
        )}
      </div>
    </div>
  )
}
