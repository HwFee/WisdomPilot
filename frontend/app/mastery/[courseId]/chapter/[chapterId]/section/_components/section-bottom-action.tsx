'use client'

import { Play, ArrowRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageContainer } from '@/components/layout'

interface SectionBottomActionProps {
  saving: boolean
  onStartQuiz: () => void
}

export function SectionBottomAction({ saving, onStartQuiz }: SectionBottomActionProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-background border-t">
      <PageContainer className="p-4">
        <Button
          type="button"
          onClick={onStartQuiz}
          disabled={saving}
          className="w-full"
        >
          {saving ? (
            <Loader2 strokeWidth={1.5} className="size-5 animate-spin" />
          ) : (
            <>
              <Play strokeWidth={1.5} className="size-5 mr-2" />
              小节测试
              <ArrowRight strokeWidth={1.5} className="size-4 ml-2" />
            </>
          )}
        </Button>
      </PageContainer>
    </div>
  )
}
