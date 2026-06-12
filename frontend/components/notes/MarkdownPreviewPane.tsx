'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github-dark.css'
import { Eye } from 'lucide-react'
import { translate } from './note-translate'

interface MarkdownPreviewPaneProps {
  content: string
  lang: 'zh' | 'en'
  variant: 'fullPage' | 'modal'
}

export function MarkdownPreviewPane({ content, lang, variant }: MarkdownPreviewPaneProps) {
  const proseClass = variant === 'fullPage' ? 'prose prose-lg' : 'prose prose-sm'

  if (variant === 'fullPage') {
    return (
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-center px-6 py-3 text-sm text-muted-foreground border-b border-border">
          <div className="flex items-center gap-2">
            <Eye className="size-4" strokeWidth={1.5} />
            <span>{translate(lang, '实时预览', 'Live Preview')}</span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <div className={`${proseClass} dark:prose-invert max-w-none`}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex, rehypeHighlight]}
              components={{
                h1: ({ children }) => <h1 className="text-3xl font-semibold mt-6 mb-3">{children}</h1>,
                h2: ({ children }) => <h2 className="text-2xl font-semibold mt-5 mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-xl font-semibold mt-4 mb-2">{children}</h3>,
                h4: ({ children }) => <h4 className="text-lg font-semibold mt-3 mb-1">{children}</h4>,
                h5: ({ children }) => <h5 className="text-base font-semibold mt-2 mb-1">{children}</h5>,
                h6: ({ children }) => (
                  <h6 className="text-sm font-semibold mt-2 mb-1 text-muted-foreground">{children}</h6>
                ),
                p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-primary pl-4 my-3 italic text-muted-foreground">
                    {children}
                  </blockquote>
                ),
                code: ({ className, children, ...props }) => {
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
                pre: ({ children }) => <pre className="bg-muted p-4 rounded-lg overflow-x-auto my-3">{children}</pre>,
                a: ({ href, children }) => (
                  <a href={href} className="text-primary underline hover:text-primary/80">
                    {children}
                  </a>
                ),
                table: ({ children }) => <table className="w-full border-collapse my-3">{children}</table>,
                th: ({ children }) => (
                  <th className="border border-border px-3 py-2 bg-muted font-semibold text-left">{children}</th>
                ),
                td: ({ children }) => <td className="border border-border px-3 py-2">{children}</td>,
              }}
            >
              {content || translate(lang, '暂无内容', 'No content yet')}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="flex items-center justify-center mb-2 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Eye className="size-4" strokeWidth={1.5} />
          <span>{translate(lang, '预览', 'Preview')}</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 border border-border">
        <div className={`${proseClass} dark:prose-invert max-w-none`}>
          <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex, rehypeHighlight]}>
            {content || translate(lang, '暂无内容', 'No content yet')}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
