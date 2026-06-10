'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Clock, BookOpen, CheckCircle, Play, Loader2, ArrowRight } from 'lucide-react'
import { CodeRunner } from '@/components/mastery/CodeRunner'
import { getSection, saveSectionProgress, type SectionDetail, type KnowledgePointDetail } from '@/lib/api/sections'
import { getStoredToken } from '@/lib/api'
import { KnowledgeOrb } from '@/components/ui/knowledge-orb'
import { cn } from '@/lib/utils'
import { LazyMotion, domAnimation, m, AnimatePresence } from 'framer-motion'
import { getLanguageId } from './lib/section-utils'
import { useLearningSession } from './hooks/use-learning-session'
import { KnowledgePointCard } from './components/knowledge-point-card'

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

  const { transferSession } = useLearningSession(sectionId, section)

  useEffect(() => {
    loadSection()
  }, [sectionId])

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

    transferSession()

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

  const handleOpenRunner = (kpId: number, initialCode: string, languageId: number) => {
    setUiState(prev => ({ ...prev, activeRunnerKpId: kpId }))
    if (!kpEditorStates.has(kpId)) {
      setKpEditorStates(prev => {
        const next = new Map(prev)
        next.set(kpId, { code: initialCode, languageId })
        return next
      })
    }
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
              {section.knowledge_points.map((kp, index) => (
                <KnowledgePointCard
                  key={kp.id}
                  kp={kp}
                  index={index}
                  isExpanded={expandedKp === kp.id}
                  sectionKnowledgePoints={section.knowledge_points}
                  onToggle={toggleKp}
                  onOpenRunner={handleOpenRunner}
                />
              ))}
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
