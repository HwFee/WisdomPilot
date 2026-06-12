'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getSection, saveSectionProgress, type SectionDetail } from '@/lib/api/sections'
import { getStoredToken } from '@/lib/api'
import { KnowledgeOrb } from '@/components/ui/knowledge-orb'
import { cn } from '@/lib/utils'
import { useLearningSession } from './hooks/use-learning-session'
import { PageContainer } from '@/components/layout'
import { SectionPageHeader } from '../_components/section-page-header'
import { SectionMainContent } from '../_components/section-main-content'
import { SectionRunnerPanel } from '../_components/section-runner-panel'
import { SectionKnowledgePanel } from '../_components/section-knowledge-panel'
import { SectionBottomAction } from '../_components/section-bottom-action'

export default function MasterySectionClient() {
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

    loadSection()
  }, [sectionId, courseId, chapterId, push])

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

  const handleCodeChange = (kpId: number, code: string) => {
    setKpEditorStates((prev) => {
      const next = new Map(prev)
      const existing = next.get(kpId)
      next.set(kpId, {
        code,
        languageId: existing?.languageId ?? next.get(kpId)?.languageId ?? 0,
      })
      return next
    })
  }

  const handleLanguageChange = (kpId: number, languageId: number) => {
    setKpEditorStates((prev) => {
      const next = new Map(prev)
      const existing = next.get(kpId)
      next.set(kpId, {
        code: existing?.code ?? next.get(kpId)?.code ?? '',
        languageId,
      })
      return next
    })
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
          <Button type="button" variant="link" onClick={handleBack}>
            返回
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("min-h-screen bg-background", activeRunnerKpId !== null && "h-screen flex flex-col overflow-hidden")}>
      <SectionPageHeader
        section={section}
        activeRunnerKpId={activeRunnerKpId}
        onBack={handleBack}
        showBackButton={activeRunnerKpId === null}
      />

      {activeRunnerKpId !== null ? (
        <div className="flex flex-1 overflow-hidden">
          <main className="w-2/5 overflow-y-auto flex flex-col">
            <div className="sticky top-0 z-10 bg-background border-b px-4 py-3 flex items-center gap-3 flex-shrink-0">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={handleBack}
                aria-label="返回"
              >
                <ArrowLeft strokeWidth={1.5} className="size-5" />
              </Button>
              <span className="text-sm text-muted-foreground">知识点列表</span>
            </div>
            <div className="flex-1 overflow-y-auto">
              <SectionKnowledgePanel
                knowledgePoints={section.knowledge_points}
                expandedKp={expandedKp}
                saving={saving}
                onToggle={toggleKp}
                onOpenRunner={handleOpenRunner}
                onStartQuiz={handleStartQuiz}
              />
            </div>
          </main>

          <SectionRunnerPanel
            activeRunnerKpId={activeRunnerKpId}
            knowledgePoints={section.knowledge_points}
            editorStates={kpEditorStates}
            onClose={() => setUiState(prev => ({ ...prev, activeRunnerKpId: null }))}
            onCodeChange={handleCodeChange}
            onLanguageChange={handleLanguageChange}
          />
        </div>
      ) : (
        <main className="py-6 pb-32">
          <PageContainer className="space-y-6">
            <SectionMainContent section={section} sectionId={sectionId} />

            <SectionKnowledgePanel
              knowledgePoints={section.knowledge_points}
              expandedKp={expandedKp}
              saving={saving}
              onToggle={toggleKp}
              onOpenRunner={handleOpenRunner}
              onStartQuiz={handleStartQuiz}
            />
          </PageContainer>
        </main>
      )}

      {activeRunnerKpId === null && (
        <SectionBottomAction saving={saving} onStartQuiz={handleStartQuiz} />
      )}

      <KnowledgeOrb
        courseId={courseId}
        chapterId={chapterId}
        sectionId={sectionId}
      />
    </div>
  )
}