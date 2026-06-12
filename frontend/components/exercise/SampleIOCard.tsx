'use client'

import { useState } from 'react'
import { Play, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react'
import { Panel } from '@/components/layout/Panel'
import { Button } from '@/components/ui/button'

interface SampleIOCardProps {
  input: string
  output: string
  onRun?: (input: string) => void
  isRunning?: boolean
  lang?: 'zh' | 'en'
}

export function SampleIOCard({
  input,
  output,
  onRun,
  isRunning = false,
  lang = 'zh',
}: SampleIOCardProps) {
  const [copied, setCopied] = useState<'input' | 'output' | null>(null)
  const [expanded, setExpanded] = useState(true)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleCopy = async (text: string, type: 'input' | 'output') => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(type)
      setTimeout(() => setCopied(null), 2000)
    } catch (err) {
      // Fallback for non-secure contexts (e.g. HTTP localhost)
      try {
        const textarea = document.createElement('textarea')
        textarea.value = text
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
        setCopied(type)
        setTimeout(() => setCopied(null), 2000)
      } catch (fallbackErr) {
        console.error('Failed to copy:', fallbackErr)
      }
    }
  }

  return (
    <Panel>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-muted hover:bg-secondary transition-colors border-b border-border"
      >
        <span className="text-sm font-medium text-foreground">
          {t('样例', 'Sample')}
        </span>
        {expanded ? (
          <ChevronUp className="size-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="size-4 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-border">
          {/* Input */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-primary uppercase tracking-wide">
                {t('输入', 'Input')}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleCopy(input, 'input')}
                  className="flex items-center gap-1 px-2 py-1 text-xs text-muted-foreground hover:text-primary hover:bg-muted rounded transition-colors"
                  title={t('复制', 'Copy')}
                >
                  {copied === 'input' ? (
                    <Check className="size-3.5 text-success" />
                  ) : (
                    <Copy className="size-3.5" />
                  )}
                  {copied === 'input' ? t('已复制', 'Copied') : t('复制', 'Copy')}
                </button>
                {onRun && (
                  <Button
                    type="button"
                    size="sm"
                    variant="success"
                    onClick={() => onRun(input)}
                    disabled={isRunning}
                    className="h-7 px-2.5 text-xs"
                  >
                    <Play className="size-3.5" />
                    {isRunning ? t('运行中...', 'Running...') : t('运行', 'Run')}
                  </Button>
                )}
              </div>
            </div>
            <div className="bg-zinc-900 text-zinc-100 border border-zinc-700/50 rounded p-3">
              <pre className="text-sm font-mono whitespace-pre-wrap">{input || '(空)'}</pre>
            </div>
          </div>

          {/* Output */}
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-success uppercase tracking-wide">
                {t('输出', 'Output')}
              </span>
              <button
                type="button"
                onClick={() => handleCopy(output, 'output')}
                className="flex items-center gap-1 px-2 py-1 text-xs text-muted-foreground hover:text-primary hover:bg-muted rounded transition-colors"
                title={t('复制', 'Copy')}
              >
                {copied === 'output' ? (
                  <Check className="size-3.5 text-success" />
                ) : (
                  <Copy className="size-3.5" />
                )}
                {copied === 'output' ? t('已复制', 'Copied') : t('复制', 'Copy')}
              </button>
            </div>
            <div className="bg-zinc-900 text-zinc-100 border border-zinc-700/50 rounded p-3">
              <pre className="text-sm font-mono whitespace-pre-wrap">{output || '(空)'}</pre>
            </div>
          </div>
        </div>
      )}
    </Panel>
  )
}

// Multiple samples component
interface SampleIOListProps {
  samples: Array<{ input: string; output: string }>
  onRun?: (input: string) => void
  isRunning?: boolean
  lang?: 'zh' | 'en'
}

function SampleIOList({
  samples,
  onRun,
  isRunning = false,
  lang = 'zh',
}: SampleIOListProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  if (samples.length === 0) return null

  if (samples.length === 1) {
    return (
      <SampleIOCard
        input={samples[0].input}
        output={samples[0].output}
        onRun={onRun}
        isRunning={isRunning}
        lang={lang}
      />
    )
  }

  return (
    <div className="flex flex-col gap-y-3">
      {samples.map((sample, index) => (
        <div key={`sample-${sample.input.slice(0, 30)}`}>
          <div className="text-xs text-muted-foreground mb-1.5 ml-1">
            {t('样例', 'Sample')} {index + 1}
          </div>
          <SampleIOCard
            input={sample.input}
            output={sample.output}
            onRun={onRun}
            isRunning={isRunning}
            lang={lang}
          />
        </div>
      ))}
    </div>
  )
}
