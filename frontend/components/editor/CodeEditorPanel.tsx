'use client'

import { useRef, useState, useCallback, forwardRef as forwardRefReact, useImperativeHandle } from 'react'
import Editor, { OnMount, OnChange } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import { cn } from '@/lib/utils'
import { executeCode, CodeExecutionResponse, LANGUAGE_CONFIG } from '@/lib/code-api'
import { getStoredToken } from '@/lib/api'
import { Play, Save, Loader2, ChevronDown, X } from 'lucide-react'

export interface CodeEditorPanelProps {
  defaultCode?: string
  defaultLanguage?: number
  chapterId?: number
  subsectionIndex?: number
  onCodeChange?: (code: string) => void
  onClose?: () => void
  className?: string
}

export interface CodeEditorPanelRef {
  getCode: () => string
  setCode: (code: string) => void
  getLanguage: () => number
}

const LANGUAGES = [
  { id: 71, name: 'Python 3' },
  { id: 63, name: 'JavaScript' },
  { id: 74, name: 'TypeScript' },
  { id: 50, name: 'C' },
  { id: 54, name: 'C++' },
]

const CodeEditorPanel = forwardRefReact<CodeEditorPanelRef, CodeEditorPanelProps>(
  (
    {
      defaultCode = '',
      defaultLanguage = 71,
      chapterId,
      subsectionIndex,
      onCodeChange,
      onClose,
      className,
    },
    ref
  ) => {
    const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)
    const [code, setCodeState] = useState(defaultCode)
    const [language, setLanguage] = useState(defaultLanguage)
    const [isRunning, setIsRunning] = useState(false)
    const [output, setOutput] = useState<CodeExecutionResponse | null>(null)
    const [isLanguageMenuOpen, setIsLanguageMenuOpen] = useState(false)

    // Expose methods via ref
    useImperativeHandle(ref, () => ({
      getCode: () => code,
      setCode: (newCode: string) => {
        setCodeState(newCode)
        editorRef.current?.setValue(newCode)
      },
      getLanguage: () => language,
    }))

    const handleEditorMount: OnMount = (editor, monaco) => {
      editorRef.current = editor
      // Configure editor settings
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

    const handleChange: OnChange = (value) => {
      const newCode = value || ''
      setCodeState(newCode)
      onCodeChange?.(newCode)
    }

    const handleRun = useCallback(async () => {
      const token = getStoredToken()
      if (!token) return

      setIsRunning(true)
      setOutput(null)

      try {
        const result = await executeCode(token, {
          code,
          language_id: language,
          stdin: '',
        })
        setOutput(result)
      } catch (error) {
        setOutput({
          token: '',
          status: 'error',
          status_id: -1,
          stdout: null,
          stderr: null,
          compile_output: null,
          message: error instanceof Error ? error.message : 'Execution failed',
          time: null,
          memory: null,
          exit_code: -1,
        })
      } finally {
        setIsRunning(false)
      }
    }, [code, language])

    const handleSave = useCallback(() => {
      // TODO: Implement code saving to backend
    }, [chapterId, subsectionIndex, code, language])

    const selectedLanguageLabel = LANGUAGE_CONFIG[language]?.label || 'Python'

    const getStatusColor = (statusId: number) => {
      switch (statusId) {
        case 3: return 'text-green-400' // Accepted
        case 4: return 'text-red-400' // Wrong Answer
        case 5: return 'text-red-500' // Compilation Error
        case 8: return 'text-yellow-400' // Time Limit Exceeded
        case 9: return 'text-yellow-500' // Memory Limit Exceeded
        case 6:
        case 7:
        case 10:
        case 11: return 'text-orange-400' // Runtime Error
        case 12:
        case 13: return 'text-red-500' // System Error
        default: return 'text-gray-400'
      }
    }

    const getOutputColor = (outputData: CodeExecutionResponse) => {
      const statusId = outputData.status_id
      if (statusId === 3) return 'text-green-400' // Accepted
      if (statusId === 5 || statusId === 12 || statusId === 13) return 'text-red-400' // Error
      if (statusId === 8 || statusId === 9) return 'text-yellow-400' // Warning
      if (statusId >= 6 && statusId <= 11) return 'text-orange-400' // Runtime Error
      if (outputData.message) return 'text-red-400'
      return 'text-green-400'
    }

    return (
      <div className={cn('flex flex-col h-full bg-gray-900', className)}>
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
          {/* Language selector */}
          <div className="relative">
            <button
              onClick={() => setIsLanguageMenuOpen(!isLanguageMenuOpen)}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 text-white text-sm rounded hover:bg-gray-700"
            >
              {selectedLanguageLabel}
              <ChevronDown className="w-4 h-4" />
            </button>
            {isLanguageMenuOpen && (
              <div className="absolute top-full left-0 mt-1 bg-gray-800 border border-gray-700 rounded shadow-lg z-10">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.id}
                    onClick={() => {
                      setLanguage(lang.id)
                      setIsLanguageMenuOpen(false)
                    }}
                    className={cn(
                      'block w-full px-4 py-2 text-sm text-left hover:bg-gray-700',
                      language === lang.id ? 'text-blue-400' : 'text-white'
                    )}
                  >
                    {lang.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex gap-2">
            <button
              onClick={handleRun}
              disabled={isRunning || !code.trim()}
              className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunning ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              运行
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              <Save className="w-4 h-4" />
              保存
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-600 text-white text-sm rounded hover:bg-gray-500"
              >
                <X className="w-4 h-4" />
                关闭
              </button>
            )}
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1 min-h-0">
          <Editor
            height="100%"
            language={LANGUAGE_CONFIG[language]?.monacoLanguage || 'python'}
            value={code}
            onChange={handleChange}
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

        {/* Output panel - 洛谷风格 */}
        <div className="border-t border-gray-700 bg-gray-800 max-h-56 overflow-y-auto">
          <div className="px-4 py-2 border-b border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-gray-300">Output</span>
              {output && (
                <span className={cn('text-sm font-medium', getStatusColor(output.status_id))}>
                  {output.status}
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              {output?.time && (
                <span>Time: {output.time}s</span>
              )}
              {output?.memory && (
                <span>Memory: {output.memory}KB</span>
              )}
            </div>
          </div>
          <div className="p-4 font-mono text-sm">
            {!output ? (
              <span className="text-gray-500">点击&quot;运行&quot;执行您的代码</span>
            ) : (
              <div>
                {/* Status line */}
                <div className={cn('mb-2', getStatusColor(output.status_id))}>
                  {output.status}
                </div>
                {/* Separator */}
                <div className="border-t border-gray-600 my-2" />
                {/* Output content */}
                {output.message ? (
                  <pre className="whitespace-pre-wrap">{output.message}</pre>
                ) : output.stdout ? (
                  <pre className={cn('whitespace-pre-wrap', getOutputColor(output))}>
                    {output.stdout}
                  </pre>
                ) : output.stderr ? (
                  <pre className="text-yellow-400 whitespace-pre-wrap">{output.stderr}</pre>
                ) : output.compile_output ? (
                  <pre className="text-red-400 whitespace-pre-wrap">{output.compile_output}</pre>
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
)

CodeEditorPanel.displayName = 'CodeEditorPanel'

export { CodeEditorPanel }
