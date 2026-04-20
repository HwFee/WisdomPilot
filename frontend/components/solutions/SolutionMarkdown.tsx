'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github-dark.css'

interface SolutionMarkdownProps {
  content: string
}

export function SolutionMarkdown({ content }: SolutionMarkdownProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex, rehypeHighlight]}
      components={{
        code: ({ className, children, ...props }) => {
          const isInline = !className
          if (isInline) {
            return (
              <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-foreground" {...props}>
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
        pre: ({ children }) => (
          <pre className="bg-[#0d1117] rounded-xl p-4 overflow-x-auto text-sm my-4">
            {children}
          </pre>
        ),
        p: ({ children }) => (
          <p className="text-foreground leading-relaxed mb-4">{children}</p>
        ),
        h1: ({ children }) => <h1 className="text-2xl font-bold text-foreground mt-8 mb-4">{children}</h1>,
        h2: ({ children }) => <h2 className="text-xl font-semibold text-foreground mt-6 mb-3">{children}</h2>,
        h3: ({ children }) => <h3 className="text-lg font-semibold text-foreground mt-4 mb-2">{children}</h3>,
        ul: ({ children }) => <ul className="list-disc list-inside space-y-2 my-4">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside space-y-2 my-4">{children}</ol>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground my-4">
            {children}
          </blockquote>
        ),
        a: ({ href, children }) => (
          <a href={href} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
            {children}
          </a>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}