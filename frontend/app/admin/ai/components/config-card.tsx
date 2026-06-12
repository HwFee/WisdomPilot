'use client'

import React from 'react'
import { Loader2, Save, Zap, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Panel } from '@/components/layout/Panel'
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
  const testButtonVariant = isTesting
    ? { icon: Loader2, iconClassName: 'animate-spin', label: '测试中...' }
    : { icon: Zap, iconClassName: '', label: '测试连接' }

  const saveButtonVariant = isSaving
    ? { icon: Loader2, iconClassName: 'animate-spin', label: '保存中...' }
    : { icon: Save, iconClassName: '', label: '保存配置' }

  const resultVariant = testResult
    ? testResult.success
      ? { icon: CheckCircle, className: 'text-success', message: testResult.message }
      : { icon: AlertCircle, className: 'text-destructive', message: testResult.message }
    : null

  return (
    <Panel className="p-6 flex flex-col gap-y-5">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg text-primary">{icon}</div>
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="flex flex-col gap-y-5">
        {children}
        <div className="flex items-center gap-3 pt-2 border-t border-border">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onTest}
            disabled={isTesting}
            className="border-primary text-primary hover:bg-primary/10"
          >
            <testButtonVariant.icon className={cn('size-4 mr-1.5', testButtonVariant.iconClassName)} />
            {testButtonVariant.label}
          </Button>
          {resultVariant && (
            <div className={cn('flex items-center gap-2 text-sm', resultVariant.className)}>
              <resultVariant.icon className="size-4" />
              <span>{resultVariant.message}</span>
              {testResult?.latency_ms !== undefined && (
                <span className="text-xs text-muted-foreground">({testResult.latency_ms}ms)</span>
              )}
            </div>
          )}
        </div>
      </div>
      <Button
        type="button"
        onClick={onSave}
        disabled={isSaving}
        className="self-start"
      >
        <saveButtonVariant.icon className={cn('size-4 mr-2', saveButtonVariant.iconClassName)} />
        {saveButtonVariant.label}
      </Button>
    </Panel>
  )
}
