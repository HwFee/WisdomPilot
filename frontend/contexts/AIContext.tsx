'use client'

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

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

// Knowledge point context for the knowledge learning orb
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

// ========================================
// Context Interface
// ========================================

export interface AIContextState {
  // Exercise panel state (for exercise/arena pages)
  activeQuestion: CurrentExerciseContext | null
  isPanelOpen: boolean
  panelSpawnPos: { x: number; y: number } | null
  openPanel: (question: CurrentExerciseContext, spawnPos?: { x: number; y: number }) => void
  closePanel: () => void

  // Knowledge orb state (for mastery pages)
  activeKnowledgeQuestion: ActiveKnowledgeQuestion | null
  isKnowledgePanelOpen: boolean
  knowledgePanelSpawnPos: { x: number; y: number } | null
  openKnowledgePanel: (question: ActiveKnowledgeQuestion, spawnPos?: { x: number; y: number }) => void
  closeKnowledgePanel: () => void
}

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
  // Exercise panel state (for exercise/arena pages)
  const [activeQuestion, setActiveQuestion] = useState<CurrentExerciseContext | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [panelSpawnPos, setPanelSpawnPos] = useState<{ x: number; y: number } | null>(null)

  // Knowledge orb state (for mastery pages)
  const [activeKnowledgeQuestion, setActiveKnowledgeQuestion] = useState<ActiveKnowledgeQuestion | null>(null)
  const [isKnowledgePanelOpen, setIsKnowledgePanelOpen] = useState(false)
  const [knowledgePanelSpawnPos, setKnowledgePanelSpawnPos] = useState<{ x: number; y: number } | null>(null)

  const openPanel = useCallback((question: CurrentExerciseContext, spawnPos?: { x: number; y: number }) => {
    setActiveQuestion({ ...question })
    setIsPanelOpen(true)
    setPanelSpawnPos(spawnPos ?? null)
  }, [])

  const closePanel = useCallback(() => {
    setIsPanelOpen(false)
  }, [])

  const openKnowledgePanel = useCallback((question: ActiveKnowledgeQuestion, spawnPos?: { x: number; y: number }) => {
    setActiveKnowledgeQuestion({ ...question })
    setIsKnowledgePanelOpen(true)
    setKnowledgePanelSpawnPos(spawnPos ?? null)
  }, [])

  const closeKnowledgePanel = useCallback(() => {
    setIsKnowledgePanelOpen(false)
  }, [])

  return (
    <AIContext.Provider value={{
      activeQuestion,
      isPanelOpen,
      panelSpawnPos,
      openPanel,
      closePanel,
      activeKnowledgeQuestion,
      isKnowledgePanelOpen,
      knowledgePanelSpawnPos,
      openKnowledgePanel,
      closeKnowledgePanel,
    }}>
      {children}
    </AIContext.Provider>
  )
}
