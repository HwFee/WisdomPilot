'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Clock, BookOpen, CheckCircle, Play, Loader2, ArrowRight } from 'lucide-react'
import { CodeRunner } from '@/components/mastery/CodeRunner'
import { getSection, saveSectionProgress, type SectionDetail } from '@/lib/api/sections'
import { getStoredToken } from '@/lib/api'
import { KnowledgeOrb } from '@/components/ui/knowledge-orb'
import { cn } from '@/lib/utils'
import { LazyMotion, domAnimation, m, AnimatePresence } from 'framer-motion'
import { getLanguageId } from './lib/section-utils'
import { useLearningSession } from './hooks/use-learning-session'
import { KnowledgePointCard } from './components/knowledge-point-card'
import { PageContainer, Grid, Panel, PanelHeader } from '@/components/layout'

export const metadata = {
  title: '小节学习 - 智码领航',
  description: '学习知识点与小节测试',
}

export default function SectionLearningPage() {
  const params = useParams()
  const { push } = useRouter()
  const courseId = parseInt(params.courseId as string)
  const chapterId = parseInt(params.chapterId as string)
  const sectionId = parseInt(params.sectionId as string)

  const [section, setSection] = useState<SectionDetail | null>(null)
  const [asyncState, setAsyncState] = useState({ loading: true, saving: false, error: null as string | null })
  const [uiState, setUiState] = useState({ expandedKp: null as number | null, activeRunnerKpId: null as number | null })
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

      if (response.section.knowledge_points && response.section.knowledge_points.length > 0) {
        setUiState(prev => ({ ...prev, expandedKp: response.section.knowledge_points[0].id }))
      }

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
      push(`/mastery/${courseId}?chapter=${chapterId}&section=${sectionId}&fromSection=${sectionId}&continueSession=1`)
    } catch {
      // Progress save failed - continue anyway
    } finally {
      setAsyncState(prev => ({ ...prev, saving: false }))
    }
  }

  const handleBack = () => {
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
        <Loader2 strokeWidth={1.5} className="size-8 text-muted-foreground" />
      </div>
    )
  }

  if (error || !section) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || '未找到小节'}</p>
          <button type="button" onClick={handleBack} className="text-primary hover:underline">
            返回
          </button>
        </div>
      </div>
    )
  }

  const mainContent = (
    <>
      {/* Learning Objectives */}
      {section.learning_objectives && section.learning_objectives.length > 0 && (
        <Panel>
          <PanelHeader title="学习目标" />
          <div className="p-6">
            <ul className="space-y-2">
              {section.learning_objectives.map((objective) => (
                <li key={`obj-${section.id}-${objective}`} className="flex items-start gap-2 text-sm">
                  <CheckCircle strokeWidth={1.5} className="size-4 text-primary flex-shrink-0 mt-0.5" />
                  <span>{objective}</span>
                </li>
              ))}
            </ul>
          </div>
        </Panel>
      )}

      {/* Description */}
      {section.description && (
        <Panel>
          <PanelHeader title="小节介绍" />
          <div className="p-6">
            <p className="text-muted-foreground text-lg leading-relaxed">
              {section.description}
            </p>
          </div>
        </Panel>
      )}

      {/* Fallback content */}
      {(!section.knowledge_points || section.knowledge_points.length === 0) && (
        <div
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
            <div className="text-center py-12 text-muted-foreground bg-card border border-border">
              <BookOpen strokeWidth={1.5} className="size-12 mx-auto mb-4 opacity-50" />
              <p>内容正在编写中...</p>
            </div>
          )}
        </div>
      )}
    </>
  )

  return (
    <div className={cn("min-h-screen bg-background", activeRunnerKpId !== null && "h-screen flex flex-col overflow-hidden")}>
      {/* Header */}
      <header className={cn("sticky top-0 z-50 bg-background border-b", activeRunnerKpId !== null && "flex-shrink-0")}>
        <PageContainer className={cn("py-4", activeRunnerKpId !== null && "w-full")}>
          <div className="flex items-center gap-4">
            <button type="button"
              onClick={handleBack}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ArrowLeft strokeWidth={1.5} className="size-5" />
            </button>
            <div className="flex-1 min-w-0">
              <h1 className="text-lg font-semibold text-foreground truncate">
                {section.title}
              </h1>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock strokeWidth={1.5} className="size-3.5" />
                  {section.estimated_minutes} 分钟
                </span>
                {section.is_completed && (
                  <span className="flex items-center gap-1 text-emerald-600">
                    <CheckCircle strokeWidth={1.5} className="size-3.5" />
                    已完成
                  </span>
                )}
              </div>
            </div>
          </div>
        </PageContainer>
      </header>

      {activeRunnerKpId !== null ? (
        <div className="flex flex-1 overflow-hidden">
          <main className="w-2/5 overflow-y-auto p-4 space-y-6">
            {mainContent}
          </main>

          <LazyMotion features={domAnimation}>
            <AnimatePresence mode="wait">
              {section.knowledge_points && (
                <m.div
                  key="runner-panel"
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
      ) : (
        <main className="py-6 pb-32">
          <PageContainer>
            <Grid>
              {/* Main content area */}
              <div className="col-span-12 lg:col-span-8 space-y-6">
                {mainContent}
              </div>

              {/* Side panel: knowledge points + practice */}
              <aside className="col-span-12 lg:col-span-4 space-y-6">
                {section.knowledge_points && section.knowledge_points.length > 0 && (
                  <Panel>
                    <PanelHeader
                      title="知识点"
                      count={`${section.knowledge_points.length}`}
                    />
                    <div className="p-4 space-y-3">
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
                  </Panel>
                )}

                <Panel>
                  <PanelHeader title="练习" />
                  <div className="p-6">
                    <p className="text-sm text-muted-foreground mb-4">
                      完成学习后，通过小节测试巩固知识点。
                    </p>
                    <button type="button"
                      onClick={handleStartQuiz}
                      disabled={saving}
                      className="w-full flex items-center justify-center gap-2 py-3 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-70"
                    >
                      {saving ? (
                        <Loader2 strokeWidth={1.5} className="size-5" />
                      ) : (
                        <>
                          <Play strokeWidth={1.5} className="size-5" />
                          小节测试
                          <ArrowRight strokeWidth={1.5} className="size-4" />
                        </>
                      )}
                    </button>
                  </div>
                </Panel>
              </aside>
            </Grid>
          </PageContainer>
        </main>
      )}

      {/* Bottom Action Bar */}
      {activeRunnerKpId === null && (
        <div className="fixed bottom-0 left-0 right-0 bg-background border-t">
          <PageContainer className="p-4">
            <button type="button"
              onClick={handleStartQuiz}
              disabled={saving}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-70"
            >
              {saving ? (
                <Loader2 strokeWidth={1.5} className="size-5" />
              ) : (
                <>
                  <Play strokeWidth={1.5} className="size-5" />
                  小节测试
                  <ArrowRight strokeWidth={1.5} className="size-4" />
                </>
              )}
            </button>
          </PageContainer>
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
