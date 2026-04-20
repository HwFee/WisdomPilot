'use client'

import { useState, useEffect } from 'react'
import { Play, Loader2, X, Copy, Check } from 'lucide-react'

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
  const [input, setInput] = useState(defaultInput)
  const [copied, setCopied] = useState(false)

  // 当 defaultInput 改变时（比如从样例运行传入），更新输入框
  useEffect(() => {
    if (defaultInput && defaultInput !== input) {
      setInput(defaultInput)
    }
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
    <div className="custom-test-input">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#F5F7FA] border-b border-[#E4E7ED]">
        <span className="text-sm font-medium text-[#606266]">
          {t('自定义测试', 'Custom Test')}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            disabled={!input}
            className="p-1.5 text-[#909399] hover:text-[#3498DB] hover:bg-[#EBEEF5] rounded transition-colors disabled:opacity-30"
            title={t('复制', 'Copy')}
          >
            {copied ? (
              <Check className="w-4 h-4 text-[#52C41A]" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
          <button
            onClick={handleClear}
            disabled={!input}
            className="p-1.5 text-[#909399] hover:text-[#E74C3C] hover:bg-[#EBEEF5] rounded transition-colors disabled:opacity-30"
            title={t('清空', 'Clear')}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Input Area */}
      <div className="p-3 bg-white">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('输入测试数据...', 'Enter test input...')}
          className="w-full h-24 px-3 py-2 bg-[#FAFBFC] border border-[#E4E7ED] rounded-lg text-sm font-mono text-[#303133] placeholder-[#C0C4CC] focus:outline-none focus:border-[#3498DB] focus:ring-1 focus:ring-[#3498DB]/20 resize-none"
          spellCheck={false}
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-[#909399]">
            {t('Ctrl+Enter 运行', 'Ctrl+Enter to run')}
          </span>
          <button
            onClick={handleRun}
            disabled={isRunning || !input.trim()}
            className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium text-white bg-[#52C41A] hover:bg-[#27AE60] rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                {t('运行中...', 'Running...')}
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                {t('运行', 'Run')}
              </>
            )}
          </button>
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
      <div className="test-output-display running">
        <div className="flex items-center justify-center py-6">
          <Loader2 className="w-5 h-5 animate-spin text-[#3498DB]" />
          <span className="ml-2 text-sm text-[#606266]">{t('运行中...', 'Running...')}</span>
        </div>
      </div>
    )
  }

  if (!output && !error) {
    return null
  }

  return (
    <div className={`test-output-display ${passed ? 'passed' : error ? 'error' : 'failed'}`}>
      {passed !== undefined && (
        <div className={`status-bar ${passed ? 'accepted' : 'wrong'}`}>
          {passed ? (
            <span className="text-[#52C41A] font-medium">✓ {t('通过', 'Accepted')}</span>
          ) : (
            <span className="text-[#E74C3C] font-medium">✗ {t('答案错误', 'Wrong Answer')}</span>
          )}
        </div>
      )}

      {error ? (
        <div className="p-3">
          <span className="text-xs font-medium text-[#E74C3C] uppercase tracking-wide mb-1.5 block">
            {t('错误', 'Error')}
          </span>
          <pre className="text-xs font-mono text-[#E74C3C] whitespace-pre-wrap">{error}</pre>
        </div>
      ) : (
        <div className="p-3">
          <span className="text-xs font-medium text-[#52C41A] uppercase tracking-wide mb-1.5 block">
            {t('输出', 'Output')}
          </span>
          <pre className="text-xs font-mono text-[#303133] whitespace-pre-wrap">{output || '(空)'}</pre>

          {expected !== undefined && !passed && (
            <div className="mt-3 pt-3 border-t border-[#E4E7ED]">
              <span className="text-xs font-medium text-[#3498DB] uppercase tracking-wide mb-1.5 block">
                {t('期望', 'Expected')}
              </span>
              <pre className="text-xs font-mono text-[#303133] whitespace-pre-wrap">{expected || '(空)'}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
