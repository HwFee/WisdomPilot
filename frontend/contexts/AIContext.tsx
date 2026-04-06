'use client'

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { getStoredToken } from '@/lib/api'
import { getChoiceAnalysis, getCodeFeedback, getChoiceExplanation, type ChoiceAnalysisRequest, type CodeFeedbackRequest, type ChoiceExplanationRequest } from '@/lib/ai-api'

// ========================================
// Types
// ========================================

export type ExerciseType = 'choice' | 'programming' | null

export interface CurrentExerciseContext {
  type: ExerciseType
  chapterId: number
  subsectionIndex: number
  exerciseId: number
  question?: string
  options?: string[]
  selectedAnswer?: number
  correctAnswer?: number
  code?: string
  language?: string
  exerciseDescription?: string
  expectedOutput?: string
  actualOutput?: string
  status?: string
  errorMessage?: string
  answerStatus?: "unanswered" | "correct" | "wrong"
}

export interface AIAnalysisResult {
  analysis?: string
  diagnosis?: string
  suggestions?: string
  optimizedCode?: string
  is_correct?: boolean
  explanation?: string
}

export interface AIContextState {
  currentExercise: CurrentExerciseContext | null
  setCurrentExercise: (ctx: CurrentExerciseContext | null) => void
  hintLoading: boolean
  hintResult: string | null
  analysisLoading: boolean
  analysisResult: AIAnalysisResult | null
  feedbackLoading: boolean
  feedbackResult: AIAnalysisResult | null
  triggerHint: () => Promise<void>
  triggerAnalysis: () => Promise<void>
  triggerFeedback: () => Promise<void>
  clearResults: () => void
  // Panel state for new floating launcher
  activeQuestion: CurrentExerciseContext | null
  isPanelOpen: boolean
  panelSpawnPos: { x: number; y: number } | null
  openPanel: (question: CurrentExerciseContext, spawnPos?: { x: number; y: number }) => void
  closePanel: () => void
}

// ========================================
// Context
// ========================================

const AIContext = createContext<AIContextState | null>(null)

export function useAIContext(): AIContextState {
  const ctx = useContext(AIContext)
  if (!ctx) {
    throw new Error('useAIContext must be used within AIContextProvider')
  }
  return ctx
}

// ========================================
// Provider
// ========================================

export function AIContextProvider({ children }: { children: ReactNode }) {
  const [currentExercise, setCurrentExercise] = useState<CurrentExerciseContext | null>(null)
  const [hintLoading, setHintLoading] = useState(false)
  const [hintResult, setHintResult] = useState<string | null>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AIAnalysisResult | null>(null)
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  const [feedbackResult, setFeedbackResult] = useState<AIAnalysisResult | null>(null)

  // Panel state for floating launcher
  const [activeQuestion, setActiveQuestion] = useState<CurrentExerciseContext | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [panelSpawnPos, setPanelSpawnPos] = useState<{ x: number; y: number } | null>(null)

  const openPanel = useCallback((question: CurrentExerciseContext, spawnPos?: { x: number; y: number }) => {
    // Clone to avoid mutation if caller mutates after call
    setActiveQuestion({ ...question })
    setIsPanelOpen(true)
    setPanelSpawnPos(spawnPos || null)
  }, [])

  const closePanel = useCallback(() => {
    setIsPanelOpen(false)
  }, [])

  const clearResults = useCallback(() => {
    setHintResult(null)
    setAnalysisResult(null)
    setFeedbackResult(null)
  }, [])

  const triggerHint = useCallback(async () => {
    if (!currentExercise || currentExercise.type !== 'choice') return

    setHintLoading(true)
    setHintResult(null)

    const token = getStoredToken()
    if (!token) {
      setHintLoading(false)
      return
    }

    try {
      const request: ChoiceExplanationRequest = {
        chapter_id: currentExercise.chapterId,
        subsection_index: currentExercise.subsectionIndex,
        exercise_id: currentExercise.exerciseId,
        question: currentExercise.question || '',
        options: currentExercise.options || [],
        user_selected_index: currentExercise.selectedAnswer ?? -1,
        correct_index: currentExercise.correctAnswer ?? -1,
      }
      const response = await getChoiceExplanation(token, request)
      setHintResult(response.explanation)
    } catch (error) {
      console.error('[AI] 获取提示失败:', error)
      setHintResult('获取 AI 提示失败，请重试。')
    } finally {
      setHintLoading(false)
    }
  }, [currentExercise])

  const triggerAnalysis = useCallback(async () => {
    if (!currentExercise || currentExercise.type !== 'choice') return

    setAnalysisLoading(true)
    setAnalysisResult(null)

    const token = getStoredToken()
    if (!token) {
      setAnalysisLoading(false)
      return
    }

    try {
      const request: ChoiceAnalysisRequest = {
        question_text: currentExercise.question || '',
        options: currentExercise.options || [],
        user_selected: currentExercise.selectedAnswer ?? -1,
        correct_answer: currentExercise.correctAnswer ?? -1,
        chapter_id: currentExercise.chapterId,
        exercise_id: String(currentExercise.exerciseId),
      }
      const response = await getChoiceAnalysis(token, request)
      setAnalysisResult({
        analysis: response.analysis,
        is_correct: response.is_correct,
      })
    } catch (error) {
      console.error('[AI] 获取分析失败:', error)
      setAnalysisResult({ analysis: '获取 AI 分析失败，请重试。', is_correct: false })
    } finally {
      setAnalysisLoading(false)
    }
  }, [currentExercise])

  const triggerFeedback = useCallback(async () => {
    if (!currentExercise || currentExercise.type !== 'programming') return

    setFeedbackLoading(true)
    setFeedbackResult(null)

    const token = getStoredToken()
    if (!token) {
      setFeedbackLoading(false)
      return
    }

    try {
      const request: CodeFeedbackRequest = {
        code: currentExercise.code || '',
        language: currentExercise.language || 'python',
        exercise_description: currentExercise.exerciseDescription || '',
        expected_output: currentExercise.expectedOutput || '',
        actual_output: currentExercise.actualOutput || '',
        status: currentExercise.status || '',
        error_message: currentExercise.errorMessage || '',
        chapter_id: currentExercise.chapterId,
        exercise_id: String(currentExercise.exerciseId),
      }
      const response = await getCodeFeedback(token, request)
      setFeedbackResult({
        diagnosis: response.diagnosis,
        suggestions: response.suggestions,
        optimizedCode: response.optimized_code,
      })
    } catch (error) {
      console.error('[AI] 获取反馈失败:', error)
      setFeedbackResult({ diagnosis: '获取 AI 反馈失败，请重试。', suggestions: '', optimizedCode: currentExercise.code || '' })
    } finally {
      setFeedbackLoading(false)
    }
  }, [currentExercise])

  return (
    <AIContext.Provider value={{
      currentExercise,
      setCurrentExercise,
      hintLoading,
      hintResult,
      analysisLoading,
      analysisResult,
      feedbackLoading,
      feedbackResult,
      triggerHint,
      triggerAnalysis,
      triggerFeedback,
      clearResults,
      activeQuestion,
      isPanelOpen,
      panelSpawnPos,
      openPanel,
      closePanel,
    }}>
      {children}
    </AIContext.Provider>
  )
}
