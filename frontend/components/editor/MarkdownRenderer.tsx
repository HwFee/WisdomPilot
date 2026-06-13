'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github-dark.css'

interface MarkdownRendererProps {
  content: string
}

const markdownComponents = {
  h1: ({ children }: { children?: React.ReactNode }) => <h1 className="text-3xl font-semibold mt-6 mb-3">{children}</h1>,
  h2: ({ children }: { children?: React.ReactNode }) => <h2 className="text-2xl font-semibold mt-5 mb-2">{children}</h2>,
  h3: ({ children }: { children?: React.ReactNode }) => <h3 className="text-xl font-semibold mt-4 mb-2">{children}</h3>,
  h4: ({ children }: { children?: React.ReactNode }) => <h4 className="text-lg font-semibold mt-3 mb-1">{children}</h4>,
  h5: ({ children }: { children?: React.ReactNode }) => <h5 className="text-base font-semibold mt-2 mb-1">{children}</h5>,
  h6: ({ children }: { children?: React.ReactNode }) => (
    <h6 className="text-sm font-semibold mt-2 mb-1 text-muted-foreground">{children}</h6>
  ),
  p: ({ children }: { children?: React.ReactNode }) => <p className="mb-3 leading-relaxed">{children}</p>,
  ul: ({ children }: { children?: React.ReactNode }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
  ol: ({ children }: { children?: React.ReactNode }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
  li: ({ children }: { children?: React.ReactNode }) => <li className="leading-relaxed">{children}</li>,
  blockquote: ({ children }: { children?: React.ReactNode }) => (
    <blockquote className="border-l-2 border-primary pl-4 my-3 italic text-muted-foreground">{children}</blockquote>
  ),
  code: ({ className, children, ...props }: React.ComponentProps<'code'>) => {
    const isInline = !className
    return isInline ? (
      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
        {children}
      </code>
    ) : (
      <code className={className} {...props}>
        {children}
      </code>
    )
  },
  pre: ({ children }: { children?: React.ReactNode }) => (
    <pre className="bg-muted p-4 rounded-lg overflow-x-auto my-3">{children}</pre>
  ),
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => (
    <a href={href} className="text-primary underline hover:text-primary/80">
      {children}
    </a>
  ),
  table: ({ children }: { children?: React.ReactNode }) => <table className="w-full border-collapse my-3">{children}</table>,
  th: ({ children }: { children?: React.ReactNode }) => (
    <th className="border border-border px-3 py-2 bg-muted font-semibold text-left">{children}</th>
  ),
  td: ({ children }: { children?: React.ReactNode }) => <td className="border border-border px-3 py-2">{children}</td>,
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex, rehypeHighlight]}
      components={markdownComponents}
    >
      {content || ''}
    </ReactMarkdown>
  )
}
