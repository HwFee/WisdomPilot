'use client'

import { Children } from 'react'
import { BookOpen, Code, Terminal, Lightbulb, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import { MermaidBlock } from './mermaid-block'
import { getLanguageId } from '../lib/section-utils'
import type { KnowledgePointDetail } from '@/lib/api/sections'

interface KnowledgePointCardProps {
  kp: KnowledgePointDetail
  index: number
  isExpanded: boolean
  sectionKnowledgePoints?: KnowledgePointDetail[]
  onToggle: (kpId: number) => void
  onOpenRunner: (kpId: number, initialCode: string, languageId: number) => void
}

const difficultyStyles = [
  'bg-secondary text-emerald-600',
  'bg-secondary text-primary',
  'bg-secondary text-amber-600',
  'bg-muted text-red-600',
  'bg-muted text-red-600',
]
const difficultyLabels = ['入门', '基础', '中等', '进阶', '困难']

export function KnowledgePointCard({
  kp,
  index,
  isExpanded,
  sectionKnowledgePoints,
  onToggle,
  onOpenRunner,
}: KnowledgePointCardProps) {
  // 构建相邻知识点列表
  const adjacentPoints: Array<{ id: string; title: string }> = []
  if (sectionKnowledgePoints) {
    for (let i = 0; i < sectionKnowledgePoints.length; i++) {
      if (i === index - 1 || i === index + 1) {
        const p = sectionKnowledgePoints[i]
        adjacentPoints.push({ id: String(p.id), title: p.name })
      }
    }
  }

  // 构建示例代码列表
  const examples: string[] = []
  if (kp.code_example) examples.push(kp.code_example)

  return (
    <div
      className="bg-card rounded-lg border overflow-hidden transition-colors hover:border-primary knowledge-point-zone"
      data-knowledge-point
      data-knowledge-point-id={String(kp.id)}
      data-knowledge-point-title={kp.name}
      data-knowledge-point-content={kp.content || kp.summary || ''}
      data-knowledge-point-examples={JSON.stringify(examples)}
      data-knowledge-point-difficulty={kp.difficulty}
      data-knowledge-point-index={index}
      data-knowledge-point-adjacent={JSON.stringify(adjacentPoints)}
    >
      {/* 知识点标题栏 - 始终可见 */}
      <button
        type="button"
        onClick={() => onToggle(kp.id)}
        className="w-full p-4 flex items-center gap-4 text-left hover:bg-muted transition-colors"
      >
        {/* 序号 */}
        <div className="flex-shrink-0 size-8 rounded-lg bg-secondary text-primary font-bold flex items-center justify-center text-sm">
          {index + 1}
        </div>

        {/* 标题和标签 */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-foreground text-lg truncate">{kp.name}</h3>
          {kp.summary && !isExpanded && (
            <p className="text-sm text-muted-foreground mt-1 line-clamp-1">{kp.summary}</p>
          )}
        </div>

        {/* 难度标签 */}
        <span
          className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
            difficultyStyles[kp.difficulty - 1] || difficultyStyles[0]
          }`}
        >
          {difficultyLabels[kp.difficulty - 1] || '入门'}
        </span>

        {/* 展开/收起图标 */}
        <div className="flex-shrink-0 text-muted-foreground">
          {isExpanded ? <ChevronUp strokeWidth={1.5} className="size-5" /> : <ChevronDown strokeWidth={1.5} className="size-5" />}
        </div>
      </button>

      {/* 展开内容 */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-border">
          {/* 详细讲解 */}
          {kp.content && (
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-2">
                <BookOpen strokeWidth={1.5} className="size-4 text-primary" />
                <span className="font-medium text-foreground">讲解</span>
              </div>
              <div className="text-muted-foreground leading-relaxed pl-6 markdown-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex, rehypeHighlight]}
                  components={{
                    code({ className, children, ...props }) {
                      const isInline = !className
                      if (isInline) {
                        return (
                          <code
                            className="bg-muted text-foreground px-1.5 py-0.5 rounded text-sm font-mono"
                            {...props}
                          >
                            {children}
                          </code>
                        )
                      }
                      if (className?.includes('language-mermaid')) {
                        const codeText = String(children).replace(/\n$/, '')
                        return <MermaidBlock code={codeText} />
                      }
                      return (
                        <code className={`${className || ''} bg-transparent p-0`} {...props}>
                          {children}
                        </code>
                      )
                    },
                    pre({ children }) {
                      const childArr = Children.toArray(children)
                      const isMermaid = childArr.some((c: any) => c?.type?.isMermaid)
                      if (isMermaid) {
                        return <>{children}</>
                      }
                      return (
                        <pre className="bg-secondary text-foreground rounded-lg p-4 font-mono text-sm overflow-x-auto my-3 not-prose">
                          {children}
                        </pre>
                      )
                    },
                    h1: ({ children }) => <h1 className="text-xl font-semibold text-foreground mb-2 mt-4">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-semibold text-foreground mb-2 mt-3">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-medium text-foreground mb-1 mt-2">{children}</h3>,
                    ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>,
                    li: ({ children }) => <li className="text-muted-foreground">{children}</li>,
                    p: ({ children }) => <p className="mb-2 last:mb-0 text-muted-foreground">{children}</p>,
                    blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/30 pl-4 italic my-2">{children}</blockquote>,
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-3">
                        <table className="min-w-full border-collapse border border-border">{children}</table>
                      </div>
                    ),
                    thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                    tbody: ({ children }) => <tbody>{children}</tbody>,
                    tr: ({ children }) => <tr className="border-b border-border">{children}</tr>,
                    th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-foreground">{children}</th>,
                    td: ({ children }) => <td className="px-3 py-2 text-sm text-muted-foreground">{children}</td>,
                  }}
                >
                  {kp.content}
                </ReactMarkdown>
              </div>
            </div>
          )}

          {/* 代码示例 */}
          {kp.code_example && (
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-2">
                <Code strokeWidth={1.5} className="size-4 text-primary" />
                <span className="font-medium text-foreground">代码示例</span>
              </div>
              <div className="pl-6">
                <ReactMarkdown
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    pre({ children }) {
                      return (
                        <pre className="bg-secondary text-foreground rounded-lg p-4 font-mono text-sm overflow-x-auto my-0">
                          {children}
                        </pre>
                      )
                    },
                    code({ className, children, ...props }) {
                      return (
                        <code className={`${className || ''} bg-transparent p-0`} {...props}>
                          {children}
                        </code>
                      )
                    },
                  }}
                >
                  {`\`\`\`${kp.code_language || ''}\n${kp.code_example}\n\`\`\``}
                </ReactMarkdown>
              </div>
              {kp.code_explanation && (
                <p className="text-sm text-muted-foreground mt-2 pl-6">{kp.code_explanation}</p>
              )}
              {/* 在线运行按钮 */}
              <div className="mt-3 pl-6">
                <button
                  type="button"
                  onClick={() => {
                    const langId = getLanguageId(kp.code_language)
                    onOpenRunner(kp.id, kp.code_example || '', langId)
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-secondary text-primary text-sm rounded-lg hover:bg-muted transition-colors border border-border"
                >
                  <Terminal strokeWidth={1.5} className="size-3.5" />
                  在线运行
                </button>
              </div>
            </div>
          )}

          {/* 学习提示 */}
          {kp.tips && kp.tips.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb strokeWidth={1.5} className="size-4 text-amber-600" />
                <span className="font-medium text-foreground">学习提示</span>
              </div>
              <ul className="space-y-1 pl-6">
                {kp.tips.map((tip) => (
                  <li key={`tip-${kp.id}-${tip}`} className="text-sm text-muted-foreground flex items-start gap-2">
                    <span className="text-amber-600 mt-1">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 常见错误 */}
          {kp.common_mistakes && kp.common_mistakes.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle strokeWidth={1.5} className="size-4 text-red-600" />
                <span className="font-medium text-foreground">常见错误</span>
              </div>
              <ul className="space-y-1 pl-6">
                {kp.common_mistakes.map((mistake) => (
                  <li key={`mistake-${kp.id}-${mistake}`} className="text-sm text-muted-foreground flex items-start gap-2">
                    <span className="text-red-600 mt-1">•</span>
                    <span>{mistake}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
