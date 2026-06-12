'use client'

import { LazyMotion, domAnimation, m, AnimatePresence } from 'framer-motion'
import { CodeRunner } from '@/components/mastery/CodeRunner'
import { getLanguageId } from '../[sectionId]/lib/section-utils'
import type { KnowledgePointDetail } from '@/lib/api/sections'

interface SectionRunnerPanelProps {
  activeRunnerKpId: number
  knowledgePoints: KnowledgePointDetail[]
  editorStates: Map<number, { code: string; languageId: number }>
  onClose: () => void
  onCodeChange: (kpId: number, code: string) => void
  onLanguageChange: (kpId: number, languageId: number) => void
}

export function SectionRunnerPanel({
  activeRunnerKpId,
  knowledgePoints,
  editorStates,
  onClose,
  onCodeChange,
  onLanguageChange,
}: SectionRunnerPanelProps) {
  const kp = knowledgePoints.find((k) => k.id === activeRunnerKpId)
  if (!kp) return null

  const state = editorStates.get(activeRunnerKpId)
  const initialCode = state?.code ?? (kp.code_example || '')
  const initialLangId = state?.languageId ?? getLanguageId(kp.code_language)

  return (
    <LazyMotion features={domAnimation}>
      <AnimatePresence mode="wait">
        <m.div
          key="runner-panel"
          className="w-3/5 p-4 flex flex-col"
        >
          <CodeRunner
            key={activeRunnerKpId}
            initialCode={initialCode}
            initialLanguageId={initialLangId}
            onClose={onClose}
            onCodeChange={(newCode) => onCodeChange(activeRunnerKpId, newCode)}
            onLanguageChange={(newLangId) => onLanguageChange(activeRunnerKpId, newLangId)}
          />
        </m.div>
      </AnimatePresence>
    </LazyMotion>
  )
}
