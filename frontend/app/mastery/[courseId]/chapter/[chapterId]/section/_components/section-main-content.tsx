'use client'

import { CheckCircle, BookOpen } from 'lucide-react'
import { Panel, PanelHeader } from '@/components/layout'
import type { SectionDetail } from '@/lib/api/sections'

interface SectionMainContentProps {
  section: SectionDetail
  sectionId: number
}

export function SectionMainContent({ section, sectionId }: SectionMainContentProps) {
  return (
    <>
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
}
