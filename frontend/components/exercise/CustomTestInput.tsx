'use client'

import { useState, useEffect } from 'react'
import { Play, Loader2, X, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface CustomTestInputProps {
  onRun: (input: string) => Promise<void>
  isRunning?: boolean
  defaultInput?: string
  lang?: 'zh' | 'en'
}

export function CustomTestInput({
  onRun,
  isRunning = false,
  defaultInput = '',
  lang = 'zh',
}: CustomTestInputProps) {
  const [input, setInput] = useState(() => defaultInput)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    setInput(defaultInput)
  }, [defaultInput])

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleRun = async () => {
    if (isRunning) return
    await onRun(input)
  }

  const handleClear = () => {
    setInput('')
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(input)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleRun()
    }
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-muted border-b border-border">
        <span className="text-sm font-medium text-foreground">
          {t('测试', 'Test')}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            disabled={!input}
            className="p-1.5 text-muted-foreground hover:text-primary hover:bg-secondary rounded transition-colors disabled:opacity-30"
            title={t('复制', 'Copy')}
          >
            {copied ? (
              <Check className="size-4 text-success" />
            ) : (
              <Copy className="size-4" />
            )}
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={!input}
            className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-secondary rounded transition-colors disabled:opacity-30"
            title={t('清空', 'Clear')}
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {/* Input Area */}
      <div className="p-3 bg-card">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('输入测试数据...', 'Enter test input...')}
          aria-label={t('测试输入', 'Test input')}
          className="w-full h-24 px-3 py-2 bg-background border border-border rounded-lg text-sm font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 resize-none"
          spellCheck={false}
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-muted-foreground">
            {t('Ctrl+Enter 运行', 'Ctrl+Enter to run')}
          </span>
          <Button
            type="button"
            variant="success"
            size="sm"
            onClick={handleRun}
            disabled={isRunning || !input.trim()}
          >
            {isRunning ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                {t('运行中...', 'Running...')}
              </>
            ) : (
              <>
                <Play className="size-4" />
                {t('运行', 'Run')}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

// Output display component
interface TestOutputDisplayProps {
  output?: string
  expected?: string
  passed?: boolean
  isRunning?: boolean
  error?: string
  lang?: 'zh' | 'en'
}

export function TestOutputDisplay({
  output,
  expected,
  passed,
  isRunning = false,
  error,
  lang = 'zh',
}: TestOutputDisplayProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  if (isRunning) {
    return (
      <div className="bg-card border border-primary/30 rounded-lg overflow-hidden">
        <div className="flex items-center justify-center py-6">
          <Loader2 className="size-5 animate-spin text-primary" />
          <span className="ml-2 text-sm text-muted-foreground">{t('运行中...', 'Running...')}</span>
        </div>
      </div>
    )
  }

  if (!output && !error) {
    return null
  }

  return (
    <div
      className={
        passed
          ? 'bg-card border border-success/30 rounded-lg overflow-hidden'
          : error
          ? 'bg-card border border-destructive/30 rounded-lg overflow-hidden'
          : 'bg-card border border-border rounded-lg overflow-hidden'
      }
    >
      {passed !== undefined && (
        <div
          className={
            passed
              ? 'px-3 py-2.5 border-b border-success/20 bg-success/5'
              : 'px-3 py-2.5 border-b border-destructive/20 bg-destructive/5'
          }
        >
          {passed ? (
            <span className="text-success font-medium">✓ {t('通过', 'Accepted')}</span>
          ) : (
            <span className="text-destructive font-medium">✗ {t('答案错误', 'Wrong Answer')}</span>
          )}
        </div>
      )}

      {error ? (
        <div className="p-3">
          <span className="text-xs font-medium text-destructive uppercase tracking-wide mb-1.5 block">
            {t('错误', 'Error')}
          </span>
          <pre className="text-xs font-mono text-destructive whitespace-pre-wrap">{error}</pre>
        </div>
      ) : (
        <div className="p-3">
          <span className="text-xs font-medium text-success uppercase tracking-wide mb-1.5 block">
            {t('输出', 'Output')}
          </span>
          <pre className="text-xs font-mono text-foreground whitespace-pre-wrap">{output || '(空)'}</pre>

          {expected !== undefined && !passed && (
            <div className="mt-3 pt-3 border-t border-border">
              <span className="text-xs font-medium text-primary uppercase tracking-wide mb-1.5 block">
                {t('期望', 'Expected')}
              </span>
              <pre className="text-xs font-mono text-foreground whitespace-pre-wrap">{expected || '(空)'}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
