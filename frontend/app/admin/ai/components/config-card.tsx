'use client'

import React from 'react'
import { Loader2, Save, Zap, CheckCircle, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TestConnectionResponse } from '@/lib/ai-api'

interface ConfigCardProps {
  title: string
  description: string
  icon: React.ReactNode
  isSaving: boolean
  isTesting: boolean
  testResult: TestConnectionResponse | null
  onSave: () => void
  onTest: () => void
  children: React.ReactNode
}

export function ConfigCard({
  title,
  description,
  icon,
  isSaving,
  isTesting,
  testResult,
  onSave,
  onTest,
  children,
}: ConfigCardProps) {
  return (
    <div className="bg-card rounded-lg shadow p-6 flex flex-col gap-y-5">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg text-primary">{icon}</div>
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="flex flex-col gap-y-5">
        {children}
        <div className="flex items-center gap-3 pt-2 border-t">
          <button type="button"
            onClick={onTest}
            disabled={isTesting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-primary text-primary rounded-lg hover:bg-primary/10 disabled:opacity-50 transition-colors"
          >
            {isTesting ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Zap className="size-4" />
            )}
            {isTesting ? '测试中...' : '测试连接'}
          </button>
          {testResult && (
            <div className={cn(
              'flex items-center gap-2 text-sm',
              testResult.success ? 'text-emerald-600' : 'text-red-500'
            )}>
              {testResult.success ? (
                <CheckCircle className="size-4" />
              ) : (
                <AlertCircle className="size-4" />
              )}
              <span>{testResult.message}</span>
              {testResult.latency_ms !== undefined && (
                <span className="text-xs text-muted-foreground">({testResult.latency_ms}ms)</span>
              )}
            </div>
          )}
        </div>
      </div>
      <button type="button"
        onClick={onSave}
        disabled={isSaving}
        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
        {isSaving ? '保存中...' : '保存配置'}
      </button>
    </div>
  )
}
