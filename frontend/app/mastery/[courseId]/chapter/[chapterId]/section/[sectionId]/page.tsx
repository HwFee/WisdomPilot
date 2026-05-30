'use client'

import { useState, useEffect, useRef, useCallback, Children } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Clock, BookOpen, CheckCircle, Play, Loader2, ArrowRight, Lightbulb, AlertTriangle, Code, ChevronDown, ChevronUp, Terminal } from 'lucide-react'
import { CodeRunner } from '@/components/mastery/CodeRunner'
import { CODE_LANGUAGE_TO_ID } from '@/lib/code-api'
import { getSection, saveSectionProgress, type SectionDetail, type KnowledgePointDetail } from '@/lib/api/sections'
import { getStoredToken } from '@/lib/api'
import { startLearningSession, endLearningSessionKeepalive } from '@/lib/api/stats'
import { KnowledgeOrb } from '@/components/ui/knowledge-orb'
import { cn } from '@/lib/utils'
import { LazyMotion, domAnimation, m, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import mermaid from 'mermaid'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeHighlight from 'rehype-highlight'

// Mermaid diagram renderer for knowledge point content
function MermaidBlock({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const [mermaidState, setMermaidState] = useState<{ svg: string; err: string | null }>({ svg: '', err: null })

  useEffect(() => {
    let cancelled = false
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'strict',
    })
    const render = async () => {
      try {
        const id = `mermaid-${Math.random().toString(36).slice(2)}`
        const { svg } = await mermaid.render(id, code)
        if (!cancelled) {
          setMermaidState({ svg, err: null })
        }
      } catch (e) {
        if (!cancelled) {
          setMermaidState({ svg: '', err: e instanceof Error ? e.message : 'Mermaid 渲染失败' })
        }
      }
    }
    render()
    return () => { cancelled = true }
  }, [code])

  if (mermaidState.err) {
    return (
      <div className="bg-red-950/30 border border-red-700/50 rounded-lg p-3 my-3">
        <p className="text-red-400 text-xs mb-1">流程图渲染失败</p>
        <pre className="text-red-300 text-xs whitespace-pre-wrap">{code}</pre>
      </div>
    )
  }

  return (
    <div
      ref={ref}
      className="mermaid-diagram my-3 flex justify-center bg-gray-800/50 rounded-lg p-4 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: mermaidState.svg }} /* eslint-disable-line react/no-danger */
    />
  )
}
(MermaidBlock as any).isMermaid = true

export default function SectionLearningPage() {
  const params = useParams()
  const { push } = useRouter()
  const courseId = parseInt(params.courseId as string)
  const chapterId = parseInt(params.chapterId as string)
  const sectionId = parseInt(params.sectionId as string)

  const [section, setSection] = useState<SectionDetail | null>(null)
  const [asyncState, setAsyncState] = useState({ loading: true, saving: false, error: null as string | null })
  const [uiState, setUiState] = useState({ expandedKp: null as number | null, activeRunnerKpId: null as number | null })
  const contentRef = useRef<HTMLDivElement>(null)

  // Code runner state
  const [kpEditorStates, setKpEditorStates] = useState<Map<number, { code: string; languageId: number }>>(new Map())
  const { loading, saving, error } = asyncState
  const { expandedKp, activeRunnerKpId } = uiState

  // 学习时长统计
  const sessionStartedAtRef = useRef<number | null>(null)
  const sessionInitializedRef = useRef(false)
  const sessionEndedRef = useRef(false)
  const chapterIdRef = useRef<number | null>(null)

  useEffect(() => {
    loadSection()
  }, [sectionId])

  // 开始学习会话
  const startTrackedSession = useCallback(async (chapterId: number) => {
    const token = getStoredToken()
    if (!token || sessionInitializedRef.current) return

    try {
      await startLearningSession(token, chapterId, 0)
      const now = Date.now()
      sessionStartedAtRef.current = now
      sessionInitializedRef.current = true
      sessionEndedRef.current = false
      chapterIdRef.current = chapterId
    } catch {
      // Session start failed - will retry on next interaction
    }
  }, [])

  // 结束学习会话
  const endTrackedSession = useCallback(() => {
    if (sessionEndedRef.current) {
      return
    }

    const token = getStoredToken()
    const startedAt = sessionStartedAtRef.current

    if (!token || !startedAt || !sessionInitializedRef.current) {
      return
    }

    const durationSeconds = Math.max(
      1,
      Math.floor((Date.now() - startedAt) / 1000),
    )

    sessionEndedRef.current = true
    sessionInitializedRef.current = false
    sessionStartedAtRef.current = null

    endLearningSessionKeepalive(token, durationSeconds, chapterIdRef.current ?? undefined)
  }, [])

  // 当 section 加载完成后启动会话
  useEffect(() => {
    if (section && !sessionInitializedRef.current) {
      startTrackedSession(section.chapter_id)
    }
  }, [section, startTrackedSession])

  // 使用 isMountedRef 来区分 StrictMode 的假 unmount 和真正的 unmount
  const isMountedRef = useRef(false)

  useEffect(() => {
    isMountedRef.current = true

    return () => {
      isMountedRef.current = false

      requestAnimationFrame(() => {
        if (!isMountedRef.current) {
          endTrackedSession()
        }
      })
    }
  }, [endTrackedSession])

  const loadSection = async () => {
    const token = getStoredToken()
    if (!token) {
      push('/login')
      return
    }

    try {
      setAsyncState(prev => ({ ...prev, loading: true }))
      const response = await getSection(sectionId, token)
      setSection(response.section)

      // 默认展开第一个知识点
      if (response.section.knowledge_points && response.section.knowledge_points.length > 0) {
        setUiState(prev => ({ ...prev, expandedKp: response.section.knowledge_points[0].id }))
      }

      // 自动保存进度为 content（正在学习中）
      if (response.section.last_position === 'content' && !response.section.is_completed) {
        await saveSectionProgress(sectionId, 'content', false, token)
      }
    } catch (err) {
      setAsyncState(prev => ({ ...prev, error: err instanceof Error ? err.message : '加载失败' }))
    } finally {
      setAsyncState(prev => ({ ...prev, loading: false }))
    }
  }

  const handleStartQuiz = async () => {
    const token = getStoredToken()
    if (!token) return

    // 保存会话开始时间到 localStorage，让做题页面继续使用
    if (sessionStartedAtRef.current && sessionInitializedRef.current) {
      const sessionData = {
        startedAt: sessionStartedAtRef.current,
        chapterId: chapterIdRef.current,
        fromSection: sectionId
      }
      try {
        localStorage.setItem('masterySession:v1', JSON.stringify(sessionData))
      } catch (e) {
        console.warn('Failed to save session to localStorage:', e)
      }

      // 标记会话已转移，不要在本页面结束
      sessionEndedRef.current = true
    }

    try {
      setAsyncState(prev => ({ ...prev, saving: true }))
      await saveSectionProgress(sectionId, 'quiz', false, token)

      // 跳转到主页面触发答题状态，带上章节和小节信息
      // 主页面会检测 chapter 参数并自动进入答题状态
      push(`/mastery/${courseId}?chapter=${chapterId}&section=${sectionId}&fromSection=${sectionId}&continueSession=1`)
    } catch {
      // Progress save failed - continue anyway
    } finally {
      setAsyncState(prev => ({ ...prev, saving: false }))
    }
  }

  const handleBack = () => {
    // 返回小节选择页面
    push(`/mastery/${courseId}/chapter/${chapterId}`)
  }

  const toggleKp = (kpId: number) => {
    setUiState(prev => ({ ...prev, expandedKp: prev.expandedKp === kpId ? null : kpId }))
  }

  // Map string language name to Judge0 language_id
  const getLanguageId = (lang: string): number => {
    const normalized = lang?.toLowerCase().trim() || 'python'
    return CODE_LANGUAGE_TO_ID[normalized] || 71
  }

  // 渲染知识点卡片
  const renderKnowledgePoint = (kp: KnowledgePointDetail, index: number) => {
    const isExpanded = expandedKp === kp.id
    const difficultyColors = ['bg-green-100 text-green-800', 'bg-blue-100 text-blue-800', 'bg-yellow-100 text-yellow-800', 'bg-orange-100 text-orange-800', 'bg-red-100 text-red-800']
    const difficultyLabels = ['入门', '基础', '中等', '进阶', '困难']

    // 构建相邻知识点列表
    const adjacentPoints: Array<{ id: string; title: string }> = []
    if (section?.knowledge_points) {
      for (let i = 0; i < section.knowledge_points.length; i++) {
        if (i === index - 1 || i === index + 1) {
          const p = section.knowledge_points[i]
          adjacentPoints.push({ id: String(p.id), title: p.name })
        }
      }
    }

    // 构建示例代码列表
    const examples: string[] = []
    if (kp.code_example) examples.push(kp.code_example)

    return (
      <div
        key={kp.id}
        className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden transition-all duration-200 hover:shadow-md knowledge-point-zone"
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
        <button type="button"
          onClick={() => toggleKp(kp.id)}
          className="w-full p-4 flex items-center gap-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        >
          {/* 序号 */}
          <div className="flex-shrink-0 size-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-sm">
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
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${difficultyColors[kp.difficulty - 1] || difficultyColors[0]}`}>
            {difficultyLabels[kp.difficulty - 1] || '入门'}
          </span>

          {/* 展开/收起图标 */}
          <div className="flex-shrink-0 text-muted-foreground">
            {isExpanded ? <ChevronUp className="size-5" /> : <ChevronDown className="size-5" />}
          </div>
        </button>

        {/* 展开内容 */}
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700">
            {/* 详细讲解 */}
            {kp.content && (
              <div className="mt-4">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="size-4 text-primary" />
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
                            <code className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                              {children}
                            </code>
                          )
                        }
                        // 检测 mermaid 流程图
                        if (className?.includes('language-mermaid')) {
                          const codeText = String(children).replace(/\n$/, '')
                          return <MermaidBlock code={codeText} />
                        }
                        // 代码块内的 code - 继承 pre 的样式，不要额外背景
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
                          <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm overflow-x-auto my-3 not-prose">
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
                      // 表格样式
                      table: ({ children }) => (
                        <div className="overflow-x-auto my-3">
                          <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600">{children}</table>
                        </div>
                      ),
                      thead: ({ children }) => <thead className="bg-gray-100 dark:bg-gray-700">{children}</thead>,
                      tbody: ({ children }) => <tbody>{children}</tbody>,
                      tr: ({ children }) => <tr className="border-b border-gray-200 dark:border-gray-700">{children}</tr>,
                      th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">{children}</th>,
                      td: ({ children }) => <td className="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">{children}</td>,
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
                  <Code className="size-4 text-primary" />
                  <span className="font-medium text-foreground">代码示例</span>
                </div>
                <div className="pl-6">
                  <ReactMarkdown
                    rehypePlugins={[rehypeHighlight]}
                    components={{
                      pre({ children }) {
                        return (
                          <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm overflow-x-auto my-0">
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
                      // Save current editor state before switching
                      if (activeRunnerKpId !== null) {
                        // Will be handled by CodeRunner's onClose/onCodeChange
                      }
                      setUiState(prev => ({ ...prev, activeRunnerKpId: kp.id }))
                      // Initialize state if not exists
                      if (!kpEditorStates.has(kp.id)) {
                        setKpEditorStates(prev => {
                          const next = new Map(prev)
                          next.set(kp.id, { code: kp.code_example || '', languageId: langId })
                          return next
                        })
                      }
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-lg hover:bg-primary/20 transition-colors border border-primary/20"
                  >
                    <Terminal className="size-3.5" />
                    在线运行
                  </button>
                </div>
              </div>
            )}

            {/* 学习提示 */}
            {kp.tips && kp.tips.length > 0 && (
              <div className="mt-4">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="size-4 text-amber-500" />
                  <span className="font-medium text-foreground">学习提示</span>
                </div>
                <ul className="space-y-1 pl-6">
                  {kp.tips.map((tip) => (
                    <li key={`tip-${kp.id}-${tip}`} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-amber-500 mt-1">•</span>
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
                  <AlertTriangle className="size-4 text-red-500" />
                  <span className="font-medium text-foreground">常见错误</span>
                </div>
                <ul className="space-y-1 pl-6">
                  {kp.common_mistakes.map((mistake) => (
                    <li key={`mistake-${kp.id}-${mistake}`} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-red-500 mt-1">•</span>
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

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !section) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error || '未找到小节'}</p>
          <button type="button" onClick={handleBack} className="text-primary hover:underline">
            返回
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("min-h-screen bg-background", activeRunnerKpId !== null && "h-screen flex flex-col overflow-hidden")}>
      {/* Header */}
      <header className={cn("sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b", activeRunnerKpId !== null && "flex-shrink-0")}>
        <div className={cn(
          "p-4",
          activeRunnerKpId !== null ? "w-full" : "max-w-4xl mx-auto"
        )}>
          <div className="flex items-center gap-4">
            <button type="button"
              onClick={handleBack}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ArrowLeft className="size-5" />
            </button>
            <div className="flex-1 min-w-0">
              <h1 className="text-lg font-semibold text-foreground truncate">
                {section.title}
              </h1>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="size-3.5" />
                  {section.estimated_minutes} 分钟
                </span>
                {section.is_completed && (
                  <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                    <CheckCircle className="size-3.5" />
                    已完成
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className={cn(activeRunnerKpId !== null && "flex flex-1 overflow-hidden")}>
        <main className={cn(
          "transition-all duration-300 ease-in-out",
          activeRunnerKpId !== null
            ? "w-2/5 overflow-y-auto p-4"
            : "max-w-4xl mx-auto px-4 py-6 pb-32"
        )}>
        {/* Learning Objectives */}
        {section.learning_objectives && section.learning_objectives.length > 0 && (
          <div className="bg-primary/5 rounded-xl border border-primary/20 p-4 mb-6">
            <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <BookOpen className="size-4 text-primary" />
              学习目标
            </h2>
            <ul className="space-y-2">
              {section.learning_objectives.map((objective) => (
                <li key={`obj-${section.id}-${objective}`} className="flex items-start gap-2 text-sm">
                  <CheckCircle className="size-4 text-primary flex-shrink-0 mt-0.5" />
                  <span>{objective}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Description */}
        {section.description && (
          <p className="text-muted-foreground mb-6 text-lg">
            {section.description}
          </p>
        )}

        {/* Knowledge Points Section */}
        {section.knowledge_points && section.knowledge_points.length > 0 ? (
          <div className="flex flex-col gap-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground flex items-center gap-2">
                <BookOpen className="size-5 text-primary" />
                知识点 ({section.knowledge_points.length})
              </h2>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4m10-10h-4M6 12H2m15.07-5.07l-2.83 2.83M9.76 14.24l-2.83 2.83m11.14 0l-2.83-2.83M9.76 9.76L6.93 6.93"/></svg>
                拖拽 AI 助手到知识点上可针对性提问
              </span>
            </div>
            <div className="flex flex-col gap-y-3">
              {section.knowledge_points.map((kp, index) => renderKnowledgePoint(kp, index))}
            </div>
          </div>
        ) : (
          /* Fallback: 原有的内容展示 */
          <div
            ref={contentRef}
            className="prose prose-slate dark:prose-invert max-w-none"
            data-knowledge-point
            data-knowledge-point-id={`section-${sectionId}`}
            data-knowledge-point-title={section.title}
            data-knowledge-point-content={section.content || ''}
            data-knowledge-point-examples="[]"
            data-knowledge-point-difficulty={1}
            data-knowledge-point-index={0}
            data-knowledge-point-adjacent="[]"
          >
            {section.content ? (
              <div className="text-foreground leading-relaxed">
                {section.content}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <BookOpen className="size-12 mx-auto mb-4 opacity-50" />
                <p>内容正在编写中...</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Right: Code Runner */}
      <LazyMotion features={domAnimation}>
      <AnimatePresence mode="wait">
        {activeRunnerKpId !== null && section?.knowledge_points && (
          <m.div
            key="runner-panel"
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 100, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="w-3/5 p-4 flex flex-col"
          >
            {(() => {
              const kp = section.knowledge_points.find((k) => k.id === activeRunnerKpId)
              if (!kp) return null
              const state = kpEditorStates.get(activeRunnerKpId)
              const initialCode = state?.code ?? (kp.code_example || '')
              const initialLangId = state?.languageId ?? getLanguageId(kp.code_language)
              return (
                <CodeRunner
                  key={activeRunnerKpId}
                  initialCode={initialCode}
                  initialLanguageId={initialLangId}
                  onClose={() => setUiState(prev => ({ ...prev, activeRunnerKpId: null }))}
                  onCodeChange={(newCode) => {
                    setKpEditorStates((prev) => {
                      const next = new Map(prev)
                      const existing = next.get(activeRunnerKpId)
                      next.set(activeRunnerKpId, {
                        code: newCode,
                        languageId: existing?.languageId ?? initialLangId,
                      })
                      return next
                    })
                  }}
                  onLanguageChange={(newLangId) => {
                    setKpEditorStates((prev) => {
                      const next = new Map(prev)
                      const existing = next.get(activeRunnerKpId)
                      next.set(activeRunnerKpId, {
                        code: existing?.code ?? initialCode,
                        languageId: newLangId,
                      })
                      return next
                    })
                  }}
                />
              )
            })()}
          </m.div>
        )}
      </AnimatePresence>
      </LazyMotion>
      </div>

      {/* Bottom Action Bar */}
      {activeRunnerKpId === null && (
        <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-t">
          <div className="max-w-4xl mx-auto p-4">
            <button type="button"
              onClick={handleStartQuiz}
              disabled={saving}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium bg-gradient-to-r from-primary to-primary/80 text-white hover:shadow-lg transition-all disabled:opacity-70"
            >
              {saving ? (
                <Loader2 className="size-5 animate-spin" />
              ) : (
                <>
                  <Play className="size-5" />
                  小节测试
                  <ArrowRight className="size-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* AI Knowledge Assistant Orb */}
      <KnowledgeOrb
        courseId={courseId}
        chapterId={chapterId}
        sectionId={sectionId}
      />
    </div>
  )
}
