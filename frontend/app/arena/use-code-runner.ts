'use client'

import { useState, useRef, useCallback } from 'react'
import { executeCode } from '@/lib/api/code'
import { getStoredToken } from '@/lib/api'
import { LANGUAGE_MAP } from './types'
import type { TestCaseResult, FeedbackState } from './types'

export function useCodeRunner() {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState<string>('python')
  const [feedbackState, setFeedbackState] = useState<FeedbackState>('idle')
  const [testResults, setTestResults] = useState<TestCaseResult[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [customTestInput, setCustomTestInput] = useState('')
  const [customTestOutput, setCustomTestOutput] = useState<{
    output?: string
    expected?: string
    passed?: boolean
    error?: string
  } | null>(null)
  const [isCustomRunning, setIsCustomRunning] = useState(false)
  const [rightPanelTab, setRightPanelTab] = useState<'code' | 'test' | 'output'>('code')
  const [showResultModal, setShowResultModal] = useState(false)
  const [modalResult, setModalResult] = useState<{
    isCorrect: boolean
    passedCount: number
    totalCount: number
    starsEarned: number
    promoted: boolean
    demoted: boolean
    firstTimeCorrect: boolean
    firstTimeWrong: boolean
  } | null>(null)

  const codeRef = useRef(code)
  codeRef.current = code

  const reset = useCallback(() => {
    setTestResults([])
    setFeedbackState('idle')
    setCustomTestOutput(null)
    setShowResultModal(false)
  }, [])

  const handleCustomRun = useCallback(
    async (input: string, isFromSample: boolean = false) => {
      if (!codeRef.current || isCustomRunning) return

      setIsCustomRunning(true)
      setCustomTestOutput(null)

      try {
        const token = getStoredToken()
        if (!token) return

        const result = await executeCode(
          {
            code: codeRef.current,
            language_id: LANGUAGE_MAP[language]?.id || 71,
            stdin: input,
          },
          token,
        )

        setCustomTestOutput({
          output: result.stdout || '',
          expected: undefined,
          passed: undefined,
          error: result.stderr || result.compile_output,
        })
      } catch (error) {
        console.error('Custom run failed:', error)
        setCustomTestOutput({ error: '运行失败，请重试' })
      } finally {
        setIsCustomRunning(false)
      }
    },
    [isCustomRunning, language],
  )

  const handleSampleRun = useCallback(
    async (input: string, expectedOutput?: string) => {
      setCustomTestInput(input)

      if (!codeRef.current || isCustomRunning) return

      setIsCustomRunning(true)
      setCustomTestOutput(null)

      try {
        const token = getStoredToken()
        if (!token) return

        const result = await executeCode(
          {
            code: codeRef.current,
            language_id: LANGUAGE_MAP[language]?.id || 71,
            stdin: input,
          },
          token,
        )

        const output = (result.stdout || '').trim()
        const expected = (expectedOutput || '').trim()
        const passed = output === expected

        setCustomTestOutput({
          output,
          expected,
          passed,
          error: result.stderr || result.compile_output,
        })
      } catch (error) {
        console.error('Sample run failed:', error)
        setCustomTestOutput({ error: '运行失败，请重试' })
      } finally {
        setIsCustomRunning(false)
      }
    },
    [isCustomRunning, language],
  )

  return {
    code,
    setCode,
    language,
    setLanguage,
    feedbackState,
    setFeedbackState,
    testResults,
    setTestResults,
    isSubmitting,
    setIsSubmitting,
    customTestInput,
    setCustomTestInput,
    customTestOutput,
    setCustomTestOutput,
    isCustomRunning,
    setIsCustomRunning,
    rightPanelTab,
    setRightPanelTab,
    showResultModal,
    setShowResultModal,
    modalResult,
    setModalResult,
    codeRef,
    reset,
    handleCustomRun,
    handleSampleRun,
  }
}
