'use client'

import { Panel, PanelHeader } from '@/components/layout'
import { KnowledgePointCard } from '../[sectionId]/components/knowledge-point-card'
import type { KnowledgePointDetail } from '@/lib/api/sections'

interface SectionKnowledgePanelProps {
  knowledgePoints: KnowledgePointDetail[]
  expandedKp: number | null
  saving: boolean
  onToggle: (kpId: number) => void
  onOpenRunner: (kpId: number, initialCode: string, languageId: number) => void
  onStartQuiz: () => void
}

export function SectionKnowledgePanel({
  knowledgePoints,
  expandedKp,
  onToggle,
  onOpenRunner,
}: SectionKnowledgePanelProps) {
  return (
    <div className="space-y-6">
      {knowledgePoints.length > 0 && (
        <Panel>
          <PanelHeader
            title="知识点"
            count={`${knowledgePoints.length}`}
          />
          <div className="p-4 space-y-3">
            {knowledgePoints.map((kp, index) => (
              <KnowledgePointCard
                key={kp.id}
                kp={kp}
                index={index}
                isExpanded={expandedKp === kp.id}
                sectionKnowledgePoints={knowledgePoints}
                onToggle={onToggle}
                onOpenRunner={onOpenRunner}
              />
            ))}
          </div>
        </Panel>
      )}
    </div>
  )
}
