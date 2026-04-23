/**
 * Knowledge Panel Component
 *
 * Displays chapter knowledge content for mastery path learning.
 * Shows AI-generated knowledge points with code examples.
 */

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'
import type { KnowledgeContentResponse, KnowledgePoint } from '@/types/api'

interface KnowledgePanelProps {
  content: KnowledgeContentResponse | null
  isLoading?: boolean
  onStartQuiz: () => void
  onClose: () => void
}

export function KnowledgePanel({
  content,
  isLoading = false,
  onStartQuiz,
  onClose,
}: KnowledgePanelProps) {
  const [expandedPoint, setExpandedPoint] = useState<string | null>(
    content?.knowledge_points[0]?.id || null
  )

  const togglePoint = (pointId: string) => {
    setExpandedPoint(prev => (prev === pointId ? null : pointId))
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xl">
        <div className="relative w-full max-w-2xl rounded-2xl border border-white/10 shadow-2xl bg-card/95 backdrop-blur-sm p-8 mx-4">
          {/* 顶部光效 */}
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-muted rounded w-1/2" />
            <div className="h-4 bg-muted rounded w-3/4" />
            <div className="h-4 bg-muted rounded w-2/3" />
            <div className="h-32 bg-muted rounded" />
          </div>
          <p className="text-center text-muted-foreground mt-4">加载中...</p>
        </div>
      </div>
    )
  }

  if (!content) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xl">
        <div className="relative w-full max-w-2xl rounded-2xl border border-white/10 shadow-2xl bg-card/95 backdrop-blur-sm p-8 mx-4">
          {/* 顶部光效 */}
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
          <p className="text-center text-muted-foreground">无法加载知识点内容</p>
          <button type="button"
            onClick={onClose}
            className="mt-4 w-full py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-foreground font-medium"
          >
            关闭
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xl">
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 12 }}
        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
        className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col rounded-2xl border border-white/10 shadow-2xl bg-card/95 backdrop-blur-sm"
      >
        {/* 顶部光效 */}
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

        {/* Header */}
        <div className="p-6 border-b border-border/50 flex-shrink-0 bg-gradient-to-r from-primary/5 via-primary/[0.02] to-transparent">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-foreground">{content.chapter_title}</h2>
              <p className="text-sm text-muted-foreground mt-1">知识点讲解</p>
            </div>
            <button type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg bg-muted/50 hover:bg-muted border border-border/50 hover:border-border transition-all group"
              aria-label="关闭"
            >
              <svg className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              {content.total_points} 个知识点
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              预计学习时间 {content.estimated_time} 分钟
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {content.knowledge_points.map((point, index) => (
              <KnowledgePointCard
                key={point.id}
                point={point}
                index={index}
                isExpanded={expandedPoint === point.id}
                onToggle={() => togglePoint(point.id)}
              />
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border/50 flex-shrink-0 bg-muted/30">
          <button type="button"
            onClick={onStartQuiz}
            className="w-full py-3 bg-gradient-to-r from-primary to-primary-600 text-primary-foreground rounded-xl font-medium hover:from-primary-600 hover:to-primary-700 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5 flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            开始测试
          </button>
        </div>
      </motion.div>
    </div>
  )
}

interface KnowledgePointCardProps {
  point: KnowledgePoint
  index: number
  isExpanded: boolean
  onToggle: () => void
}

function KnowledgePointCard({ point, index, isExpanded, onToggle }: KnowledgePointCardProps) {
  // Serialize data for KnowledgeOrb detection
  const adjacentPoints = point.related_points?.map((title, i) => ({
    id: `related-${i}`,
    title
  })) || []

  return (
    <motion.div
      layout
      className="border border-border/50 rounded-xl overflow-hidden hover:border-primary/30 transition-colors bg-card/50"
      data-knowledge-point
      data-knowledge-point-id={point.id}
      data-knowledge-point-title={point.title}
      data-knowledge-point-content={point.content}
      data-knowledge-point-examples={JSON.stringify(point.examples || [])}
      data-knowledge-point-difficulty={point.difficulty}
      data-knowledge-point-index={index}
      data-knowledge-point-adjacent={JSON.stringify(adjacentPoints)}
    >
      {/* Header */}
      <button type="button"
        onClick={onToggle}
        className="w-full p-4 text-left flex items-start gap-3 hover:bg-muted/50 transition-colors"
      >
        <span className="flex-shrink-0 w-6 h-6 bg-primary/10 text-primary rounded-full flex items-center justify-center text-sm font-medium">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-foreground">{point.title}</h3>
            <svg
              className={`w-5 h-5 text-muted-foreground transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <DifficultyBadge difficulty={point.difficulty} />
          </div>
        </div>
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3">
              {/* Content - Markdown rendered */}
              <div className="text-muted-foreground leading-relaxed">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex, rehypeHighlight]}
                  components={{
                    // 代码块样式
                    code({ className, children, ...props }) {
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
                    pre({ children }) {
                      return (
                        <pre className="bg-muted rounded-lg p-4 font-mono text-sm overflow-x-auto my-3 not-prose border border-border/50">
                          {children}
                        </pre>
                      )
                    },
                    // 标题样式
                    h1: ({ children }) => <h1 className="text-xl font-bold text-foreground mb-2 mt-4">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-semibold text-foreground mb-2 mt-3">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-medium text-foreground mb-1 mt-2">{children}</h3>,
                    // 列表样式
                    ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>,
                    li: ({ children }) => <li className="text-muted-foreground">{children}</li>,
                    // 段落
                    p: ({ children }) => <p className="mb-2 last:mb-0 text-muted-foreground">{children}</p>,
                    // 引用
                    blockquote: ({ children }) => <blockquote className="border-l-4 border-primary/30 pl-4 italic my-2">{children}</blockquote>,
                    // 表格样式
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-3">
                        <table className="min-w-full border-collapse border border-border">{children}</table>
                      </div>
                    ),
                    thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                    tbody: ({ children }) => <tbody>{children}</tbody>,
                    tr: ({ children }) => <tr className="border-b border-border/50">{children}</tr>,
                    th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-foreground">{children}</th>,
                    td: ({ children }) => <td className="px-3 py-2 text-sm text-muted-foreground">{children}</td>,
                  }}
                >
                  {point.content}
                </ReactMarkdown>
              </div>

              {/* Code Examples */}
              {point.examples && point.examples.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">示例代码</p>
                  <div className="space-y-1">
                    {point.examples.map((example, i) => (
                      <pre
                        key={i}
                        className="bg-muted rounded-lg p-3 font-mono text-sm overflow-x-auto border border-border/50"
                      >
                        <code>{example}</code>
                      </pre>
                    ))}
                  </div>
                </div>
              )}

              {/* Related Points */}
              {point.related_points && point.related_points.length > 0 && (
                <div className="text-sm text-muted-foreground">
                  <span className="font-medium">相关知识点：</span>
                  {point.related_points.join('、')}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function DifficultyBadge({ difficulty }: { difficulty: number }) {
  const colors = {
    1: 'bg-green-100 text-green-700',
    2: 'bg-blue-100 text-blue-700',
    3: 'bg-yellow-100 text-yellow-700',
    4: 'bg-orange-100 text-orange-700',
    5: 'bg-red-100 text-red-700',
  }

  const labels = {
    1: '入门',
    2: '基础',
    3: '中等',
    4: '较难',
    5: '困难',
  }

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[difficulty as keyof typeof colors] || colors[1]}`}>
      {labels[difficulty as keyof typeof labels] || '入门'}
    </span>
  )
}
