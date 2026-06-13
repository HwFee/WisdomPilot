'use client'

import { createContext, use, useReducer, useCallback, useMemo, type ReactNode } from 'react'
import { getStoredToken } from '@/lib/api'
import { getChoiceAnalysis, getChoiceExplanation, type ChoiceAnalysisRequest, type ChoiceExplanationRequest } from '@/lib/ai-api'

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

// ========================================
// Knowledge Point Context (for mastery pages)
// ========================================

export interface KnowledgePointContext {
  id: string
  title: string
  content: string
  examples: string[]
  difficulty: number
  index: number
  adjacentPoints: Array<{ id: string; title: string }>
}

export interface ActiveKnowledgeQuestion {
  type: "knowledge"
  knowledgePoint: KnowledgePointContext
}

export interface AIContextState {
  // Exercise context (for chapter/exercise pages)
  currentExercise: CurrentExerciseContext | null
  setCurrentExercise: (ctx: CurrentExerciseContext | null) => void
  hintLoading: boolean
  hintResult: string | null
  analysisLoading: boolean
  analysisResult: AIAnalysisResult | null
  triggerHint: () => Promise<void>
  triggerAnalysis: () => Promise<void>
  clearResults: () => void

  // Question panel state (for exercise pages - choice/fill_blank questions)
  activeQuestion: CurrentExerciseContext | null
  isPanelOpen: boolean
  panelSpawnPos: { x: number; y: number } | null
  openPanel: (question: CurrentExerciseContext, spawnPos?: { x: number; y: number }) => void
  closePanel: () => void

  // Knowledge panel state (for mastery pages - knowledge points)
  activeKnowledgeQuestion: ActiveKnowledgeQuestion | null
  isKnowledgePanelOpen: boolean
  knowledgePanelSpawnPos: { x: number; y: number } | null
  openKnowledgePanel: (question: ActiveKnowledgeQuestion, spawnPos?: { x: number; y: number }) => void
  closeKnowledgePanel: () => void
}

// ========================================
// Context
// ========================================

const AIContext = createContext<AIContextState | null>(null)

export function useAIContext(): AIContextState {
  const ctx = use(AIContext)
  if (!ctx) {
    throw new Error('useAIContext must be used within AIContextProvider')
  }
  return ctx
}

// ========================================
// State & reducer
// ========================================

interface AIState {
  currentExercise: CurrentExerciseContext | null
  hintLoading: boolean
  hintResult: string | null
  analysisLoading: boolean
  analysisResult: AIAnalysisResult | null
  activeQuestion: CurrentExerciseContext | null
  isPanelOpen: boolean
  panelSpawnPos: { x: number; y: number } | null
  activeKnowledgeQuestion: ActiveKnowledgeQuestion | null
  isKnowledgePanelOpen: boolean
  knowledgePanelSpawnPos: { x: number; y: number } | null
}

const initialState: AIState = {
  currentExercise: null,
  hintLoading: false,
  hintResult: null,
  analysisLoading: false,
  analysisResult: null,
  activeQuestion: null,
  isPanelOpen: false,
  panelSpawnPos: null,
  activeKnowledgeQuestion: null,
  isKnowledgePanelOpen: false,
  knowledgePanelSpawnPos: null,
}

type AIAction =
  | { type: 'SET_CURRENT_EXERCISE'; payload: CurrentExerciseContext | null }
  | { type: 'HINT_START' }
  | { type: 'HINT_SET'; payload: string | null }
  | { type: 'ANALYSIS_START' }
  | { type: 'ANALYSIS_SET'; payload: AIAnalysisResult | null }
  | { type: 'OPEN_PANEL'; payload: { question: CurrentExerciseContext; spawnPos?: { x: number; y: number } } }
  | { type: 'CLOSE_PANEL' }
  | { type: 'OPEN_KNOWLEDGE_PANEL'; payload: { question: ActiveKnowledgeQuestion; spawnPos?: { x: number; y: number } } }
  | { type: 'CLOSE_KNOWLEDGE_PANEL' }
  | { type: 'CLEAR_RESULTS' }

function aiReducer(state: AIState, action: AIAction): AIState {
  switch (action.type) {
    case 'SET_CURRENT_EXERCISE':
      return { ...state, currentExercise: action.payload }
    case 'HINT_START':
      return { ...state, hintLoading: true, hintResult: null }
    case 'HINT_SET':
      return { ...state, hintLoading: false, hintResult: action.payload }
    case 'ANALYSIS_START':
      return { ...state, analysisLoading: true, analysisResult: null }
    case 'ANALYSIS_SET':
      return { ...state, analysisLoading: false, analysisResult: action.payload }
    case 'OPEN_PANEL':
      return { ...state, activeQuestion: { ...action.payload.question }, isPanelOpen: true, panelSpawnPos: action.payload.spawnPos ?? null }
    case 'CLOSE_PANEL':
      return { ...state, isPanelOpen: false }
    case 'OPEN_KNOWLEDGE_PANEL':
      return { ...state, activeKnowledgeQuestion: { ...action.payload.question }, isKnowledgePanelOpen: true, knowledgePanelSpawnPos: action.payload.spawnPos ?? null }
    case 'CLOSE_KNOWLEDGE_PANEL':
      return { ...state, isKnowledgePanelOpen: false }
    case 'CLEAR_RESULTS':
      return { ...state, hintResult: null, analysisResult: null }
    default:
      return state
  }
}

// ========================================
// Provider
// ========================================

export function AIContextProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(aiReducer, initialState)

  const setCurrentExercise = useCallback((ctx: CurrentExerciseContext | null) => {
    dispatch({ type: 'SET_CURRENT_EXERCISE', payload: ctx })
  }, [])

  const openPanel = useCallback((question: CurrentExerciseContext, spawnPos?: { x: number; y: number }) => {
    dispatch({ type: 'OPEN_PANEL', payload: { question, spawnPos } })
  }, [])

  const closePanel = useCallback(() => {
    dispatch({ type: 'CLOSE_PANEL' })
  }, [])

  const openKnowledgePanel = useCallback((question: ActiveKnowledgeQuestion, spawnPos?: { x: number; y: number }) => {
    dispatch({ type: 'OPEN_KNOWLEDGE_PANEL', payload: { question, spawnPos } })
  }, [])

  const closeKnowledgePanel = useCallback(() => {
    dispatch({ type: 'CLOSE_KNOWLEDGE_PANEL' })
  }, [])

  const clearResults = useCallback(() => {
    dispatch({ type: 'CLEAR_RESULTS' })
  }, [])

  const triggerHint = useCallback(async () => {
    if (!state.currentExercise || state.currentExercise.type !== 'choice') return

    dispatch({ type: 'HINT_START' })

    const token = getStoredToken()
    if (!token) {
      dispatch({ type: 'HINT_SET', payload: null })
      return
    }

    try {
      const request: ChoiceExplanationRequest = {
        chapter_id: state.currentExercise.chapterId,
        subsection_index: state.currentExercise.subsectionIndex,
        exercise_id: state.currentExercise.exerciseId,
        question: state.currentExercise.question || '',
        options: state.currentExercise.options || [],
        user_selected_index: state.currentExercise.selectedAnswer ?? -1,
        correct_index: state.currentExercise.correctAnswer ?? -1,
      }
      const response = await getChoiceExplanation(token, request)
      dispatch({ type: 'HINT_SET', payload: response.explanation })
    } catch (error) {
      console.error('[AI] 获取提示失败:', error)
      dispatch({ type: 'HINT_SET', payload: '获取 AI 提示失败，请重试。' })
    }
  }, [state.currentExercise])

  const triggerAnalysis = useCallback(async () => {
    if (!state.currentExercise || state.currentExercise.type !== 'choice') return

    dispatch({ type: 'ANALYSIS_START' })

    const token = getStoredToken()
    if (!token) {
      dispatch({ type: 'ANALYSIS_SET', payload: null })
      return
    }

    try {
      const request: ChoiceAnalysisRequest = {
        question_text: state.currentExercise.question || '',
        options: state.currentExercise.options || [],
        user_selected: state.currentExercise.selectedAnswer ?? -1,
        correct_answer: state.currentExercise.correctAnswer ?? -1,
        chapter_id: state.currentExercise.chapterId,
        exercise_id: String(state.currentExercise.exerciseId),
      }
      const response = await getChoiceAnalysis(token, request)
      dispatch({ type: 'ANALYSIS_SET', payload: { analysis: response.analysis, is_correct: response.is_correct } })
    } catch (error) {
      console.error('[AI] 获取分析失败:', error)
      dispatch({ type: 'ANALYSIS_SET', payload: { analysis: '获取 AI 分析失败，请重试。', is_correct: false } })
    }
  }, [state.currentExercise])

  const value = useMemo(
    () => ({
      currentExercise: state.currentExercise,
      setCurrentExercise,
      hintLoading: state.hintLoading,
      hintResult: state.hintResult,
      analysisLoading: state.analysisLoading,
      analysisResult: state.analysisResult,
      triggerHint,
      triggerAnalysis,
      clearResults,
      activeQuestion: state.activeQuestion,
      isPanelOpen: state.isPanelOpen,
      panelSpawnPos: state.panelSpawnPos,
      openPanel,
      closePanel,
      activeKnowledgeQuestion: state.activeKnowledgeQuestion,
      isKnowledgePanelOpen: state.isKnowledgePanelOpen,
      knowledgePanelSpawnPos: state.knowledgePanelSpawnPos,
      openKnowledgePanel,
      closeKnowledgePanel,
    }),
    [
      state,
      setCurrentExercise,
      triggerHint,
      triggerAnalysis,
      clearResults,
      openPanel,
      closePanel,
      openKnowledgePanel,
      closeKnowledgePanel,
    ]
  )

  return (
    <AIContext.Provider value={value}>
      {children}
    </AIContext.Provider>
  )
}
