'use client'

import { useState, useCallback, useRef } from 'react'
import dynamic from 'next/dynamic'

const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false })
import { Play, Loader2, X, ChevronDown, Terminal } from 'lucide-react'
import { executeCode, LANGUAGE_CONFIG, CodeExecutionResponse } from '@/lib/code-api'
import { getStoredToken } from '@/lib/api'
import { cn } from '@/lib/utils'

interface CodeRunnerProps {
  initialCode: string
  initialLanguageId: number
  onClose: () => void
  onCodeChange?: (code: string) => void
  onLanguageChange?: (languageId: number) => void
}

const LANGUAGES = [
  { id: 71, name: 'Python 3' },
  { id: 63, name: 'JavaScript' },
  { id: 74, name: 'TypeScript' },
  { id: 50, name: 'C' },
  { id: 54, name: 'C++' },
]

function getStatusColor(statusId: number) {
  if (statusId === 3) return 'text-green-400'
  if (statusId === 5 || statusId === -1) return 'text-red-400'
  if (statusId === 8 || statusId === 9) return 'text-yellow-400'
  if (statusId >= 6 && statusId <= 11) return 'text-orange-400'
  return 'text-gray-400'
}

export function CodeRunner({
  initialCode,
  initialLanguageId,
  onClose,
  onCodeChange,
  onLanguageChange,
}: CodeRunnerProps) {
  const editorRef = useRef<import('monaco-editor').editor.IStandaloneCodeEditor | null>(null)
  const [code, setCode] = useState(() => initialCode)
  const [languageId, setLanguageId] = useState(() => initialLanguageId)
  const [runState, setRunState] = useState<{ isRunning: boolean; output: CodeExecutionResponse | null }>({ isRunning: false, output: null })
  const [uiState, setUiState] = useState({ isLangMenuOpen: false, stdin: '' })
  const { isRunning, output } = runState
  const { isLangMenuOpen, stdin } = uiState

  const handleEditorMount = (editor: import('monaco-editor').editor.IStandaloneCodeEditor) => {
    editorRef.current = editor
    editor.updateOptions({
      minimap: { enabled: false },
      fontSize: 14,
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      automaticLayout: true,
      tabSize: 4,
      wordWrap: 'on',
    })
  }

  const handleCodeChange = (value: string | undefined) => {
    const newCode = value || ''
    setCode(newCode)
    onCodeChange?.(newCode)
  }

  const handleLanguageChange = (id: number) => {
    setLanguageId(id)
    setUiState(prev => ({ ...prev, isLangMenuOpen: false }))
    onLanguageChange?.(id)
  }

  const handleRun = useCallback(async () => {
    const token = getStoredToken()
    if (!token || !code.trim()) return

    setRunState({ isRunning: true, output: null })

    try {
      const result = await executeCode(token, {
        code,
        language_id: languageId,
        stdin,
      })
      setRunState(prev => ({ ...prev, output: result }))
    } catch (error) {
      setRunState({
        isRunning: false,
        output: {
          token: '',
          status: 'Error',
          status_id: -1,
          stdout: null,
          stderr: null,
          compile_output: null,
          message: error instanceof Error ? error.message : '执行失败',
          time: null,
          memory: null,
          exit_code: -1,
        },
      })
    } finally {
      setRunState(prev => ({ ...prev, isRunning: false }))
    }
  }, [code, languageId, stdin])

  const selectedLabel = LANGUAGE_CONFIG[languageId]?.label || 'Python'

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700 bg-gray-800/50">
        {/* Language selector */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setUiState(prev => ({ ...prev, isLangMenuOpen: !prev.isLangMenuOpen }))}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 text-gray-200 text-sm rounded hover:bg-gray-600 transition-colors"
          >
            {selectedLabel}
            <ChevronDown className={cn('size-3.5 transition-transform', isLangMenuOpen && 'rotate-180')} />
          </button>
          {isLangMenuOpen && (
            <div className="absolute top-full left-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-20 min-w-[140px]">
              {LANGUAGES.map((lang) => (
                <button
                  type="button"
                  key={lang.id}
                  onClick={() => handleLanguageChange(lang.id)}
                  className={cn(
                    'block w-full px-4 py-2 text-sm text-left hover:bg-gray-700 transition-colors first:rounded-t-lg last:rounded-b-lg',
                    languageId === lang.id ? 'text-blue-400' : 'text-gray-300'
                  )}
                >
                  {lang.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRun}
            disabled={isRunning || !code.trim()}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isRunning ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <Play className="size-3.5" />
            )}
            运行
          </button>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors"
            title="收起运行器"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 min-h-0">
        <Editor
          height="100%"
          language={LANGUAGE_CONFIG[languageId]?.monacoLanguage || 'python'}
          value={code}
          onChange={handleCodeChange}
          onMount={handleEditorMount}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>

      {/* Stdin input */}
      <div className="border-t border-gray-700 bg-gray-900/50 flex-shrink-0">
        <div className="px-3 py-1.5 border-b border-gray-700/50 flex items-center gap-2">
          <Terminal className="size-3 text-gray-500" />
          <span className="text-xs font-medium text-gray-400">标准输入 (stdin)</span>
          <span className="text-[10px] text-gray-600 ml-1">程序中 input() / scanf() 会从这里读取</span>
        </div>
        <textarea
          value={stdin}
          onChange={(e) => setUiState(prev => ({ ...prev, stdin: e.target.value }))}
          placeholder="在此输入程序运行时需要的数据，每行对应一次输入..."
          aria-label="标准输入"
          className="w-full h-16 px-3 py-1.5 bg-transparent text-gray-300 text-xs font-mono resize-none focus:outline-none placeholder-gray-600"
          spellCheck={false}
        />
      </div>

      {/* Output panel */}
      <div className="border-t border-gray-700 bg-gray-800/80 max-h-[200px] overflow-y-auto">
        <div className="px-3 py-1.5 border-b border-gray-700/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-400">Output</span>
            {output && (
              <span className={cn('text-xs font-medium', getStatusColor(output.status_id))}>
                {output.status}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-[11px] text-gray-500">
            {output?.time && <span>Time: {output.time}s</span>}
            {output?.memory && <span>Memory: {output.memory}KB</span>}
          </div>
        </div>
        <div className="px-3 py-2 font-mono text-xs">
          {!output ? (
            <span className="text-gray-500">点击「运行」执行代码</span>
          ) : (
            <div>
              {output.message ? (
                <pre className="whitespace-pre-wrap text-red-400">{output.message}</pre>
              ) : output.stdout ? (
                <pre className="whitespace-pre-wrap text-green-400">{output.stdout}</pre>
              ) : output.stderr ? (
                <pre className="whitespace-pre-wrap text-yellow-400">{output.stderr}</pre>
              ) : output.compile_output ? (
                <pre className="whitespace-pre-wrap text-red-400">{output.compile_output}</pre>
              ) : (
                <span className="text-gray-500">无输出</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
