'use client'

import { useState } from 'react'
import { CheckCircle, XCircle, ChevronDown, ChevronUp, Play, Copy, Check } from 'lucide-react'

interface TestCaseResult {
  passed: boolean
  input: string
  expected: string
  actual: string
  time?: number
  memory?: number
  message?: string
}

interface TestCasesPanelProps {
  results: TestCaseResult[]
  passedCount: number
  totalCount: number
  isRunning?: boolean
  onRunTestCase?: (input: string) => void
  lang?: 'zh' | 'en'
}

export function TestCasesPanel({
  results,
  passedCount,
  totalCount,
  isRunning = false,
  onRunTestCase,
  lang = 'zh',
}: TestCasesPanelProps) {
  const [expandedCases, setExpandedCases] = useState<Set<number>>(new Set())
  const [copied, setCopied] = useState<string | null>(null)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const toggleCase = (index: number) => {
    const newExpanded = new Set(expandedCases)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedCases(newExpanded)
  }

  const handleCopy = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(id)
      setTimeout(() => setCopied(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // Overall status
  const allPassed = passedCount === totalCount
  const hasResults = results.length > 0

  if (!hasResults) return null

  return (
    <div className="test-cases-panel">
      {/* Overall Status */}
      <div className={`overall-status ${allPassed ? 'accepted' : 'wrong'}`}>
        <div className="flex items-center gap-2">
          {allPassed ? (
            <>
              <CheckCircle className="size-5 text-[#52C41A]" />
              <span className="font-bold text-[#52C41A] text-lg">
                {t('通过', 'Accepted')}
              </span>
            </>
          ) : (
            <>
              <XCircle className="size-5 text-[#E74C3C]" />
              <span className="font-bold text-[#E74C3C] text-lg">
                {t('答案错误', 'Wrong Answer')}
              </span>
            </>
          )}
        </div>
        <div className="text-sm text-[#909399]">
          {t('通过', 'Passed')} {passedCount}/{totalCount} {t('个测试点', 'test cases')}
        </div>
      </div>

      {/* Individual Test Cases */}
      <div className="test-cases-list">
        {results.map((result, index) => {
          const isExpanded = expandedCases.has(index)

          return (
            <div key={`case-${result.input.slice(0, 30)}`} className={`test-case-item ${result.passed ? 'passed' : 'failed'}`}>
              {/* Header */}
              <button type="button"
                onClick={() => toggleCase(index)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-[#F5F7FA] transition-colors"
              >
                <div className="flex items-center gap-3">
                  {result.passed ? (
                    <CheckCircle className="size-4 text-[#52C41A]" />
                  ) : (
                    <XCircle className="size-4 text-[#E74C3C]" />
                  )}
                  <span className="text-sm font-medium text-[#303133]">
                    {t('测试点', 'Test Case')} {index + 1}
                  </span>
                  {result.time && (
                    <span className="text-xs text-[#909399]">
                      {result.time}ms
                    </span>
                  )}
                  {result.memory && (
                    <span className="text-xs text-[#909399]">
                      {(result.memory / 1024).toFixed(1)}MB
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    result.passed
                      ? 'bg-[#52C41A]/10 text-[#52C41A]'
                      : 'bg-[#E74C3C]/10 text-[#E74C3C]'
                  }`}>
                    {result.passed ? t('通过', 'Passed') : t('失败', 'Failed')}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="size-4 text-[#909399]" />
                  ) : (
                    <ChevronDown className="size-4 text-[#909399]" />
                  )}
                </div>
              </button>

              {/* Details */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-[#E4E7ED]">
                  {/* Input */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-medium text-[#3498DB] uppercase tracking-wide">
                        {t('输入', 'Input')}
                      </span>
                      <div className="flex items-center gap-2">
                        <button type="button"
                          onClick={() => handleCopy(result.input, `input-${index}`)}
                          className="p-1 text-[#909399] hover:text-[#3498DB] transition-colors"
                        >
                          {copied === `input-${index}` ? (
                            <Check className="size-3.5 text-[#52C41A]" />
                          ) : (
                            <Copy className="size-3.5" />
                          )}
                        </button>
                        {onRunTestCase && (
                          <button type="button"
                            onClick={() => onRunTestCase(result.input)}
                            className="p-1 text-[#909399] hover:text-[#3498DB] transition-colors"
                            title={t('用此输入运行', 'Run with this input')}
                          >
                            <Play className="size-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="test-case-code-block">
                      <pre className="text-xs font-mono text-[#303133] whitespace-pre-wrap">
                        {result.input || '(空)'}
                      </pre>
                    </div>
                  </div>

                  {/* Expected Output */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-medium text-[#52C41A] uppercase tracking-wide">
                        {t('期望输出', 'Expected')}
                      </span>
                      <button type="button"
                        onClick={() => handleCopy(result.expected, `expected-${index}`)}
                        className="p-1 text-[#909399] hover:text-[#3498DB] transition-colors"
                      >
                        {copied === `expected-${index}` ? (
                          <Check className="size-3.5 text-[#52C41A]" />
                        ) : (
                          <Copy className="size-3.5" />
                        )}
                      </button>
                    </div>
                    <div className="test-case-code-block expected">
                      <pre className="text-xs font-mono text-[#303133] whitespace-pre-wrap">
                        {result.expected || '(空)'}
                      </pre>
                    </div>
                  </div>

                  {/* Actual Output (only show if failed) */}
                  {!result.passed && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-medium text-[#E74C3C] uppercase tracking-wide">
                          {t('实际输出', 'Actual')}
                        </span>
                        <button type="button"
                          onClick={() => handleCopy(result.actual, `actual-${index}`)}
                          className="p-1 text-[#909399] hover:text-[#3498DB] transition-colors"
                        >
                          {copied === `actual-${index}` ? (
                            <Check className="size-3.5 text-[#52C41A]" />
                          ) : (
                            <Copy className="size-3.5" />
                          )}
                        </button>
                      </div>
                      <div className="test-case-code-block actual">
                        <pre className="text-xs font-mono text-[#303133] whitespace-pre-wrap">
                          {result.actual || '(空)'}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Error Message */}
                  {result.message && !result.passed && (
                    <div className="mt-3 p-2 bg-[#E74C3C]/5 border border-[#E74C3C]/20 rounded-lg">
                      <p className="text-xs text-[#E74C3C]">{result.message}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Compact version for inline display
interface TestCasesSummaryProps {
  passedCount: number
  totalCount: number
  lang?: 'zh' | 'en'
}

export function TestCasesSummary({ passedCount, totalCount, lang = 'zh' }: TestCasesSummaryProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const allPassed = passedCount === totalCount
  const percentage = totalCount > 0 ? Math.round((passedCount / totalCount) * 100) : 0

  return (
    <div className="test-cases-summary bg-[#F5F7FA]">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-[#909399]">{t('测试点', 'Test Cases')}</span>
        <span className={`text-sm font-bold ${allPassed ? 'text-[#52C41A]' : 'text-[#E74C3C]'}`}>
          {passedCount}/{totalCount}
        </span>
      </div>
      <div className="h-1.5 bg-[#E4E7ED] rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${
            allPassed ? 'bg-[#52C41A]' : 'bg-[#E74C3C]'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
