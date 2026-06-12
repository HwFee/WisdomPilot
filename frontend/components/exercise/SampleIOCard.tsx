'use client'

import { useState } from 'react'
import { Play, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react'

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
    <div className="sample-io-card">
      {/* Header */}
      <button type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-[#F5F7FA] hover:bg-[#EBEEF5] transition-colors rounded-t-lg border-b border-[#E4E7ED]"
      >
        <span className="text-sm font-medium text-[#606266]">
          {t('样例', 'Sample')}
        </span>
        {expanded ? (
          <ChevronUp className="size-4 text-[#909399]" />
        ) : (
          <ChevronDown className="size-4 text-[#909399]" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-[#E4E7ED]">
          {/* Input */}
          <div className="p-4 border-b border-[#E4E7ED]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-[#3498DB] uppercase tracking-wide">
                {t('输入', 'Input')}
              </span>
              <div className="flex items-center gap-2">
                <button type="button"
                  onClick={() => handleCopy(input, 'input')}
                  className="flex items-center gap-1 px-2 py-1 text-xs text-[#606266] hover:text-[#3498DB] hover:bg-[#F5F7FA] rounded transition-colors"
                  title={t('复制', 'Copy')}
                >
                  {copied === 'input' ? (
                    <Check className="size-3.5 text-[#52C41A]" />
                  ) : (
                    <Copy className="size-3.5" />
                  )}
                  {copied === 'input' ? t('已复制', 'Copied') : t('复制', 'Copy')}
                </button>
                {onRun && (
                  <button type="button"
                    onClick={() => onRun(input)}
                    disabled={isRunning}
                    className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-white bg-[#52C41A] hover:bg-[#27AE60] rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="size-3.5" />
                    {isRunning ? t('运行中...', 'Running...') : t('运行', 'Run')}
                  </button>
                )}
              </div>
            </div>
            <div className="sample-code-block">
              <pre className="text-sm font-mono text-[#303133] whitespace-pre-wrap">{input || '(空)'}</pre>
            </div>
          </div>

          {/* Output */}
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-[#52C41A] uppercase tracking-wide">
                {t('输出', 'Output')}
              </span>
              <button type="button"
                onClick={() => handleCopy(output, 'output')}
                className="flex items-center gap-1 px-2 py-1 text-xs text-[#606266] hover:text-[#3498DB] hover:bg-[#F5F7FA] rounded transition-colors"
                title={t('复制', 'Copy')}
              >
                {copied === 'output' ? (
                  <Check className="size-3.5 text-[#52C41A]" />
                ) : (
                  <Copy className="size-3.5" />
                )}
                {copied === 'output' ? t('已复制', 'Copied') : t('复制', 'Copy')}
              </button>
            </div>
            <div className="sample-code-block output">
              <pre className="text-sm font-mono text-[#303133] whitespace-pre-wrap">{output || '(空)'}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
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
          <div className="text-xs text-[#909399] mb-1.5 ml-1">
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
