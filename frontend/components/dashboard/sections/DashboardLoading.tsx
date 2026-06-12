'use client'

import { Sparkles } from 'lucide-react'
import { type Language, translate } from '../dashboard-i18n'

type DashboardLoadingProps = {
  lang: Language
}

export function DashboardLoading({ lang }: DashboardLoadingProps) {
  const t = (zh: string, en: string) => translate(zh, en, lang)

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="size-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
          <Sparkles className="size-8 text-primary" />
        </div>
        <p className="text-muted-foreground">{t('加载中...', 'Loading...')}</p>
      </div>
    </div>
  )
}
