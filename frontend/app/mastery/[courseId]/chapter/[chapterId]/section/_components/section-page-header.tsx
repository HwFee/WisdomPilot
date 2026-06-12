'use client'

import { ArrowLeft, Clock, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageContainer } from '@/components/layout'
import { cn } from '@/lib/utils'
import type { SectionDetail } from '@/lib/api/sections'

interface SectionPageHeaderProps {
  section: SectionDetail
  activeRunnerKpId: number | null
  onBack: () => void
  showBackButton?: boolean
}

export function SectionPageHeader({
  section,
  activeRunnerKpId,
  onBack,
  showBackButton = true,
}: SectionPageHeaderProps) {
  return (
    <header className={cn("sticky top-0 z-50 bg-background border-b", activeRunnerKpId !== null && "flex-shrink-0")}>
      <PageContainer className={cn("py-4", activeRunnerKpId !== null && "w-full")}>
        <div className="flex items-center gap-4">
          {showBackButton && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={onBack}
              aria-label="返回"
            >
              <ArrowLeft strokeWidth={1.5} className="size-5" />
            </Button>
          )}
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
  )
}
