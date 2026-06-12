'use client'

import { useRef, useState, useCallback, useEffect, useImperativeHandle } from 'react'
import type { RefObject } from 'react'
import dynamic from 'next/dynamic'
interface MonacoEditor {
  getValue(): string
  setValue(value: string): void
  focus(): void
  updateOptions(options: Record<string, unknown>): void
  getDomNode(): HTMLElement | null
}

const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false })
import { cn } from '@/lib/utils'
import { executeCode, CodeExecutionResponse, LANGUAGE_CONFIG } from '@/lib/code-api'
import { getStoredToken } from '@/lib/api'
import { Play, Save, Loader2, ChevronDown, X } from 'lucide-react'
import { registerActiveEditor } from '@/lib/editor-registry'
export interface CodeEditorPanelProps {
  defaultCode?: string
  defaultLanguage?: number
  chapterId?: number
  subsectionIndex?: number
  exerciseQuestion?: string
  exerciseOptions?: string[]
  onCodeChange?: (code: string) => void
  onClose?: () => void
  onExerciseComplete?: (completedExercisesBySubsection: Record<number, number[]>, completedCount: number, totalCount: number) => void
  onProgrammingResult?: (isCorrect: boolean, exerciseId?: number) => void
  onProgrammingAttempt?: (isCorrect: boolean, exerciseId: number) => void  // 每次运行都自动保存结果
  className?: string
}

export interface CodeEditorPanelRef {
  getCode: () => string
  setCode: (code: string) => void
  getLanguage: () => number
  getExerciseContext: () => {
    chapterId: number
    subsectionIndex: number
    exerciseId: number
    question: string
    options?: string[]
    code: string
    language: string
    type: "choice" | "programming"
  } | null
}

const LANGUAGES = [
  { id: 71, name: 'Python 3' },
  { id: 63, name: 'JavaScript' },
  { id: 74, name: 'TypeScript' },
  { id: 50, name: 'C' },
  { id: 54, name: 'C++' },
]

function getStatusColor(statusId: number) {
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

function getOutputColor(outputData: CodeExecutionResponse) {
  const statusId = outputData.status_id
  if (statusId === 3) return 'text-green-400' // Accepted
  if (statusId === 5 || statusId === 12 || statusId === 13) return 'text-red-400' // Error
  if (statusId === 8 || statusId === 9) return 'text-yellow-400' // Warning
  if (statusId >= 6 && statusId <= 11) return 'text-orange-400' // Runtime Error
  if (outputData.message) return 'text-red-400'
  return 'text-green-400'
}

const CodeEditorPanel = ({
  defaultCode = '',
  defaultLanguage = 71,
  chapterId,
  subsectionIndex,
  exerciseQuestion = '编程题',
  exerciseOptions,
  onCodeChange,
  onClose,
  onExerciseComplete,
  onProgrammingResult,
  onProgrammingAttempt,
  className,
  ref,
}: CodeEditorPanelProps & { ref?: React.Ref<CodeEditorPanelRef> }) => {
    const editorRef = useRef<MonacoEditor | null>(null)
    // Initialize code: try to load from localStorage first, otherwise use defaultCode
    const [code, setCodeState] = useState(() => {
      if (chapterId !== undefined && subsectionIndex !== undefined) {
        const saved = localStorage.getItem(`code_${chapterId}_${subsectionIndex}_${defaultLanguage}`)
        if (saved) return saved
      }
      return defaultCode
    })
    const [language, setLanguage] = useState(() => defaultLanguage)
    const [runState, setRunState] = useState<{ isRunning: boolean; output: CodeExecutionResponse | null }>({ isRunning: false, output: null })
    const { isRunning, output } = runState
    const [isLanguageMenuOpen, setIsLanguageMenuOpen] = useState(false)

    // Register this IDE as the active editor for orb drop detection
    useEffect(() => {
      registerActiveEditor(ref as unknown as RefObject<CodeEditorPanelRef>)
      return () => registerActiveEditor(null)
    }, [ref])

    // Load saved code when language changes
    useEffect(() => {
      if (chapterId !== undefined && subsectionIndex !== undefined) {
        const saved = localStorage.getItem(`code_${chapterId}_${subsectionIndex}_${language}`)
        if (saved && saved !== code) {
          setCodeState(saved)
          editorRef.current?.setValue(saved)
        }
      }
    }, [language])

    // Expose methods via ref
    useImperativeHandle(ref, () => ({
      getCode: () => code,
      setCode: (newCode: string) => {
        setCodeState(newCode)
        editorRef.current?.setValue(newCode)
      },
      getLanguage: () => language,
      getExerciseContext: () => {
        // Read live question text from DOM (may be updated by parent)
        // Monaco's dom node structure: .monaco-editor > .overflow-guard > .monaco-editor-background
        // IDE root div is the parent of the monaco container
        const monacoDom = editorRef.current?.getDomNode()
        const monacoContainer = monacoDom?.parentElement?.parentElement?.parentElement
        const rootEl = monacoContainer?.closest?.('[data-question-context]')
        const questionText = rootEl?.getAttribute('data-question-text') ?? exerciseQuestion
        const optionsStr = rootEl?.getAttribute('data-question-options')
        const liveOptions = optionsStr ? JSON.parse(optionsStr) : exerciseOptions
        return {
          chapterId: chapterId ?? 0,
          subsectionIndex: subsectionIndex ?? 0,
          exerciseId: 0,
          question: questionText,
          options: liveOptions,
          code,
          language: LANGUAGE_CONFIG[language]?.label?.toLowerCase() ?? 'python',
          type: "programming" as const,
        }
      },
    }))

    const handleEditorMount = (editor: MonacoEditor, monaco: any) => {
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

    const onEditorValueChange = (value: string | undefined) => {
      const newCode = value || ''
      setCodeState(newCode)
      onCodeChange?.(newCode)
    }

    const handleRun = useCallback(async () => {
      const token = getStoredToken()
      if (!token) return

      setRunState({ isRunning: true, output: null })

      try {
        const result = await executeCode(token, {
          code,
          language_id: language,
          stdin: '',
        })
        setRunState(prev => ({ ...prev, output: result }))

        // Programming exercise uses id 0
        const exerciseId = 0
        const isCorrect = result.status_id === 3 // Accepted = correct

        // Always report the result (correct or wrong)
        if (onProgrammingResult) {
          onProgrammingResult(isCorrect, exerciseId)
        }

        // Auto-save result to backend (无论对错都保存)
        if (onProgrammingAttempt) {
          onProgrammingAttempt(isCorrect, exerciseId)
        }

        // If execution is successful, mark exercise as complete
        if (isCorrect && onExerciseComplete && chapterId !== undefined && subsectionIndex !== undefined) {
          const completedSubsections: Record<number, number[]> = {}
          completedSubsections[subsectionIndex] = [exerciseId]
          const totalCount = 14
          const completedCount = 1
          onExerciseComplete(completedSubsections, completedCount, totalCount)
        }
      } catch (error) {
        setRunState({
          isRunning: false,
          output: {
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
          },
        })
      } finally {
        setRunState(prev => ({ ...prev, isRunning: false }))
      }
    }, [code, language, chapterId, subsectionIndex, onExerciseComplete, onProgrammingAttempt])

    const handleSave = useCallback(() => {
      // Save code to localStorage (keyed by chapterId-subsectionIndex-language)
      if (chapterId === undefined || subsectionIndex === undefined) return
      const storageKey = `code_${chapterId}_${subsectionIndex}_${language}`
      localStorage.setItem(storageKey, code)
      // Provide visual feedback
      setRunState(prev => ({
        ...prev,
        output: {
          token: '',
          status: 'Saved',
          status_id: 3,
          stdout: '代码已保存到本地',
          stderr: null,
          compile_output: null,
          message: null,
          time: null,
          memory: null,
          exit_code: 0,
        },
      }))
    }, [chapterId, subsectionIndex, code, language])

    const selectedLanguageLabel = LANGUAGE_CONFIG[language]?.label || 'Python'

    return (
      <div
        className={cn('flex flex-col h-full bg-gray-900', className)}
        data-question-context
        data-question-type="programming"
        data-question-id={`${chapterId}-${subsectionIndex}-0`}
        data-exercise-id={0}
        data-question-text={exerciseQuestion}
        data-question-options={exerciseOptions ? JSON.stringify(exerciseOptions) : undefined}
        data-question-code={code}
        data-question-language={LANGUAGE_CONFIG[language]?.label?.toLowerCase() ?? 'python'}
      >
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
          {/* Language selector */}
          <div className="relative">
            <button type="button"
              onClick={() => setIsLanguageMenuOpen(!isLanguageMenuOpen)}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 text-white text-sm rounded hover:bg-gray-700"
            >
              {selectedLanguageLabel}
              <ChevronDown className="size-4" />
            </button>
            {isLanguageMenuOpen && (
              <div className="absolute top-full left-0 mt-1 bg-gray-800 border border-gray-700 rounded shadow-lg z-10">
                {LANGUAGES.map((lang) => (
                  <button type="button"
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
            <button type="button"
              onClick={handleRun}
              disabled={isRunning || !code.trim()}
              className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunning ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Play className="size-4" />
              )}
              运行
            </button>
            <button type="button"
              onClick={handleSave}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              <Save className="size-4" />
              保存
            </button>
            {onClose && (
              <button type="button"
                onClick={onClose}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-600 text-white text-sm rounded hover:bg-gray-500"
              >
                <X className="size-4" />
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
            onChange={onEditorValueChange}
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
        <div className="border-t border-gray-700 bg-gray-800 max-h-80 overflow-y-auto">
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

CodeEditorPanel.displayName = 'CodeEditorPanel'



export { CodeEditorPanel }
