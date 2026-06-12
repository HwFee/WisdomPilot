'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  getStoredToken,
  getChallengeProgress,
  startStageSession,
  startInfiniteSession,
  saveChallengeCode,
  appendChallengeExercises,
} from '@/lib/api'
import { getGlobalTierInfo } from '@/lib/api/tier'
import { getChallengeExerciseContent } from '@/lib/api/learning-path'
import { endLearningSessionKeepalive } from '@/lib/api/stats'
import { getCoreBalance } from '@/lib/api/core'
import { getTemplate } from '@/lib/codeTemplates'
import type { ChallengeExercise } from '@/types/api'
import {
  Exercise,
  ExerciseProgress,
  ProgressExercise,
  ChallengeProgressResponse,
  LANGUAGE_MAP,
  DIFFICULTY_NAMES,
} from './types'

export function useArenaSession() {
  const { push } = useRouter()
  const searchParams = useSearchParams()
  const getSearchParam = useCallback(
    (name: string) => searchParams.get(name),
    [searchParams],
  )
  const difficultyFromDashboard = getSearchParam('difficulty')
  const difficultyFromDashboardRef = useRef(difficultyFromDashboard)
  difficultyFromDashboardRef.current = difficultyFromDashboard
  const exerciseIndexFromReviewRef = useRef<string | null>(null)
  if (exerciseIndexFromReviewRef.current === null) {
    exerciseIndexFromReviewRef.current = getSearchParam('exerciseIndex')
  }

  const [exercises, setExercises] = useState<Exercise[]>([])
  const [exerciseProgress, setExerciseProgress] = useState<ExerciseProgress[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [initialized, setInitialized] = useState(false)
  const loading = !initialized
  const [showExerciseList, setShowExerciseList] = useState(false)

  const savedCodesRef = useRef<Record<number, Record<string, string>>>({})
  const [contentLoadingMap, setContentLoadingMap] = useState<Record<number, boolean>>({})
  const [contentErrorMap, setContentErrorMap] = useState<Record<number, string>>({})
  const loadedContentRef = useRef<Set<number>>(null!)
  if (!loadedContentRef.current) {
    loadedContentRef.current = new Set<number>()
  }
  const loadingContentRef = useRef<Set<number>>(null!)
  if (!loadingContentRef.current) {
    loadingContentRef.current = new Set<number>()
  }

  const [tierInfo, setTierInfo] = useState<{
    tier: string
    sub_tier: number
    stars: number
    full_name: string
  } | null>(null)
  const [coreBalance, setCoreBalance] = useState<number | undefined>(undefined)

  const sessionIdRef = useRef<string>('')
  const mountedRef = useRef(true)
  const sessionStartedAtRef = useRef<number | null>(null)
  const sessionEndedRef = useRef(false)
  const sessionInitializedRef = useRef(false)
  const currentDifficultyRef = useRef<number>(1)
  const currentIndexRef = useRef(currentIndex)
  currentIndexRef.current = currentIndex

  const endTrackedSession = useCallback(() => {
    if (sessionEndedRef.current) return
    const token = getStoredToken()
    const startedAt = sessionStartedAtRef.current
    if (!token || !startedAt) return
    const durationSeconds = Math.max(1, Math.round((Date.now() - startedAt) / 1000))
    sessionEndedRef.current = true
    endLearningSessionKeepalive(token, durationSeconds, undefined)
  }, [])

  const loadExerciseContent = useCallback(
    async (exerciseId: number, index: number, language: string) => {
      if (loadingContentRef.current.has(exerciseId)) return
      if (loadedContentRef.current.has(exerciseId)) return

      const token = getStoredToken()
      if (!token) return

      loadingContentRef.current.add(exerciseId)
      setContentLoadingMap((prev) => ({ ...prev, [exerciseId]: true }))
      setContentErrorMap((prev) => {
        const next = { ...prev }
        delete next[exerciseId]
        return next
      })

      try {
        const data = await getChallengeExerciseContent(exerciseId, token)
        loadedContentRef.current.add(exerciseId)
        if (!mountedRef.current) return

        const exercise = data.exercise
        const samples = exercise.content?.samples || []
        const sampleInput = samples[0]?.input || ''
        const sampleOutput = samples[0]?.output || ''

        setExercises((prev) => {
          const updated = [...prev]
          if (updated[index]) {
            updated[index] = {
              ...updated[index],
              type: (exercise.type || updated[index].type) as Exercise['type'],
              content: {
                text: exercise.content?.text || updated[index].content.title,
                title: exercise.title || updated[index].content.title,
                description: exercise.content?.description || exercise.content?.text || updated[index].content.title,
                code_template: exercise.content?.code_template || getTemplate('python'),
                sample_input: sampleInput,
                sample_output: sampleOutput,
                samples: samples.map((s: { input?: string; output?: string }) => ({
                  input: s.input || '',
                  output: s.output || '',
                })),
              },
              knowledge_points: exercise.knowledge_points || [],
              test_cases: (exercise.test_cases || []).map((tc: { input?: string; output?: string }) => ({
                input: tc.input || '',
                output: tc.output || '',
              })),
            }
          }
          return updated
        })

        if (index === currentIndexRef.current) {
          const updated = { ...savedCodesRef.current }
          const existingCode = updated[exerciseId]?.[language]
          if (!existingCode || existingCode === getTemplate('python')) {
            updated[exerciseId] = {
              ...updated[exerciseId],
              [language]: exercise.content?.code_template || getTemplate(language),
            }
            savedCodesRef.current = updated
          }
        }
      } catch (error) {
        console.error('[挑战之路] 加载题目内容失败:', error)
        const errorMsg = error instanceof Error ? error.message : '加载失败'
        setContentErrorMap((prev) => ({ ...prev, [exerciseId]: errorMsg }))
        loadedContentRef.current.delete(exerciseId)
      } finally {
        loadingContentRef.current.delete(exerciseId)
        if (mountedRef.current) {
          setContentLoadingMap((prev) => {
            const next = { ...prev }
            delete next[exerciseId]
            return next
          })
        }
      }
    },
    [],
  )

  const processProgressData = useCallback(
    (
      progressData: ChallengeProgressResponse,
      difficulty: number,
      effectiveLanguage: string,
      targetIndex?: number,
    ) => {
      if (progressData.session_id) {
        sessionIdRef.current = progressData.session_id
      }

      const isLite = progressData.exercises.length > 0 && !progressData.exercises[0]?.content

      const exerciseList: Exercise[] = progressData.exercises.map((ex: ProgressExercise) => {
        const testCases = ex.test_cases || []
        const samples = ex.content?.samples || []
        const sampleInput = samples[0]?.input || testCases[0]?.input || ''
        const sampleOutput = samples[0]?.output || testCases[0]?.output || ''
        return {
          id: ex.exercise_id,
          z_id: ex.z_id,
          type: ((ex as ProgressExercise & { type?: string }).type || 'programming') as Exercise['type'],
          difficulty: ex.difficulty || difficulty,
          content: isLite
            ? {
                title: ex.title,
                description: '',
                code_template: getTemplate(effectiveLanguage),
                sample_input: '',
                sample_output: '',
                samples: [],
              }
            : {
                text: ex.content?.text || ex.title,
                title: ex.title,
                description: ex.content?.description || ex.content?.text || ex.title,
                code_template: ex.content?.code_template || getTemplate(effectiveLanguage),
                sample_input: sampleInput,
                sample_output: sampleOutput,
                samples: samples.map((s: { input?: string; output?: string }) => ({
                  input: s.input || '',
                  output: s.output || '',
                })),
              },
          knowledge_points: ex.knowledge_points || [],
          test_cases: testCases.map((tc: { input?: string; output?: string }) => ({
            input: tc.input || '',
            output: tc.output || '',
          })),
        }
      })

      const validIndex = targetIndex !== undefined
        ? Math.min(Math.max(0, targetIndex), exerciseList.length - 1)
        : Math.min(Math.max(0, progressData.current_index || 0), exerciseList.length - 1)

      setCurrentIndex(validIndex)
      setExercises(exerciseList)
      setExerciseProgress(
        progressData.exercises.map((ex: ProgressExercise) => ({
          exercise_id: ex.exercise_id,
          exercise_index: ex.exercise_index,
          is_completed: ex.is_completed || false,
          is_correct: ex.is_correct || false,
          is_unlocked: ex.is_unlocked || false,
          saved_code: ex.saved_code || '',
          current_language: ex.current_language || 'python',
          title: ex.title || `题目 ${ex.exercise_index + 1}`,
          difficulty: ex.difficulty || difficulty,
        })),
      )

      // Initialize saved codes
      const newSavedCodes: Record<number, Record<string, string>> = {}
      progressData.exercises.forEach((ex: ProgressExercise) => {
        if (!savedCodesRef.current[ex.exercise_id]) {
          newSavedCodes[ex.exercise_id] = {
            [ex.current_language || 'python']: ex.saved_code || getTemplate(ex.current_language || 'python'),
          }
        }
      })
      savedCodesRef.current = { ...savedCodesRef.current, ...newSavedCodes }

      return { isLite, exerciseList, validIndex }
    },
    [],
  )

  const initChallenge = useCallback(async () => {
    const token = getStoredToken()
    if (!token) {
      push('/login')
      return
    }

    const difficulty = difficultyFromDashboardRef.current ? parseInt(difficultyFromDashboardRef.current) : 1
    currentDifficultyRef.current = difficulty

    try {
      const parallelTasks: Promise<unknown>[] = [
        getChallengeProgress(token).catch(() => null),
        getGlobalTierInfo().catch(() => null),
        getCoreBalance().catch(() => null),
      ]

      if (!sessionInitializedRef.current) {
        parallelTasks.push(
          startStageSession(token, 0)
            .then(() => {
              const now = Date.now()
              sessionStartedAtRef.current = now
              sessionEndedRef.current = false
              sessionInitializedRef.current = true
            })
            .catch((error) => {
              console.error('[学习时长] 启动会话失败:', error)
            }),
        )
      }

      const [progressData, tierData, balanceData] = (await Promise.all(parallelTasks)) as [
        ChallengeProgressResponse | null,
        { tier: string; sub_tier: number; stars: number; full_name: string } | null,
        { balance: number } | null,
      ]

      if (tierData) {
        // react-doctor-disable-next-line no-derived-state — tierInfo is fetched from the API, not derivable from props/state
        setTierInfo({
          tier: tierData.tier,
          sub_tier: tierData.sub_tier,
          stars: tierData.stars,
          full_name: tierData.full_name,
        })
      }
      if (balanceData) {
        setCoreBalance(balanceData.balance)
      }

      const savedLanguage = localStorage.getItem('preferred_language')
      const effectiveLanguage = savedLanguage && LANGUAGE_MAP[savedLanguage] ? savedLanguage : 'python'

      const targetIndex = exerciseIndexFromReviewRef.current
        ? parseInt(exerciseIndexFromReviewRef.current)
        : undefined

      const setupAndMaybeLoad = (pd: ChallengeProgressResponse, ti?: number) => {
        const result = processProgressData(pd, difficulty, effectiveLanguage, ti)
        if (result.isLite && result.exerciseList.length > 0) {
          loadExerciseContent(result.exerciseList[result.validIndex].id, result.validIndex, effectiveLanguage)
        }
      }

      if (progressData && progressData.exercises && progressData.exercises.length > 0) {
        setupAndMaybeLoad(progressData, targetIndex)
      } else {
        const sessionData = await startInfiniteSession({ difficulty_level: difficulty, initial_count: 3 }, token)
        if (sessionData.exercises && sessionData.exercises.length > 0) {
          const builtProgress: ChallengeProgressResponse = {
            exercises: sessionData.exercises.map((ex: ChallengeExercise, i: number) => ({
              exercise_id: ex.id,
              exercise_index: i,
              is_completed: false,
              is_correct: false,
              is_unlocked: i === 0,
              z_id: ex.z_id,
              saved_code: '',
              current_language: 'python',
              title: ex.title || `题目 ${i + 1}`,
              difficulty: ex.difficulty,
              content: ex.content,
              knowledge_points: ex.knowledge_points || [],
              test_cases: ex.test_cases || [],
            })),
            current_index: 0,
            session_id: sessionData.session_id,
          }
          setupAndMaybeLoad(builtProgress, targetIndex)
        } else {
          const newProgressData = await getChallengeProgress(token)
          setupAndMaybeLoad(newProgressData, targetIndex)
        }
      }
    } catch (error) {
      console.error('Failed to initialize challenge:', error)
      push('/dashboard')
    } finally {
      if (mountedRef.current) {
        setInitialized(true)
      }
    }
  }, [push, processProgressData, loadExerciseContent])

  const switchToExercise = useCallback(
    (index: number, language: string, onSwitch: (newCode: string) => void) => {
      if (index < 0 || index >= exercises.length) return

      const currentExercise = exercises[currentIndex]
      const targetExercise = exercises[index]

      const targetProgress = exerciseProgress.find((p) => p.exercise_id === targetExercise.id)
      if (targetProgress && !targetProgress.is_unlocked) return

      if (currentExercise) {
        savedCodesRef.current = {
          ...savedCodesRef.current,
          [currentExercise.id]: {
            ...savedCodesRef.current[currentExercise.id],
            [language]: savedCodesRef.current[currentExercise.id]?.[language] || '',
          },
        }
      }

      setCurrentIndex(index)

      const savedCodeForLang = savedCodesRef.current[targetExercise.id]?.[language]
      if (savedCodeForLang) {
        onSwitch(savedCodeForLang)
      } else {
        onSwitch(targetExercise.content.code_template || getTemplate(language))
      }

      if (!loadedContentRef.current.has(targetExercise.id) && !loadingContentRef.current.has(targetExercise.id)) {
        loadExerciseContent(targetExercise.id, index, language)
      }
    },
    [exercises, currentIndex, exerciseProgress, loadExerciseContent],
  )

  const handleNext = useCallback(() => {
    if (currentIndex < exercises.length - 1) {
      // Next will be handled by the caller with switchToExercise + reset
    }
  }, [currentIndex, exercises.length])

  const handleStay = useCallback(() => {
    // No-op, caller handles modal close
  }, [])

  const handleRetry = useCallback(() => {
    // No-op, caller handles reset
  }, [])

  const handleExitSave = useCallback(
    async (code: string, language: string) => {
      const token = getStoredToken()
      const currentExercise = exercises[currentIndex]
      if (token && currentExercise) {
        try {
          await saveChallengeCode(
            { exercise_id: currentExercise.id, code, language },
            token,
          )
        } catch (error) {
          console.error('Failed to save code on exit:', error)
        }
      }
    },
    [exercises, currentIndex],
  )

  const handleExit = useCallback(
    async (code: string, language: string) => {
      await handleExitSave(code, language)
      endTrackedSession()
      push('/dashboard')
    },
    [handleExitSave, endTrackedSession, push],
  )

  useEffect(() => {
    initChallenge()
  }, [initChallenge])

  useEffect(() => {
    const mounted = mountedRef
    return () => {
      mounted.current = false
      endTrackedSession()
    }
  }, [endTrackedSession])

  return {
    push,
    difficultyFromDashboard,
    exercises,
    exerciseProgress,
    currentIndex,
    loading,
    savedCodesRef,
    contentLoadingMap,
    contentErrorMap,
    loadedContentRef,
    loadingContentRef,
    tierInfo,
    coreBalance,
    sessionIdRef,
    currentDifficultyRef,
    endTrackedSession,
    initChallenge,
    processProgressData,
    loadExerciseContent,
    switchToExercise,
    handleNext,
    handleStay,
    handleRetry,
    handleExitSave,
    handleExit,
    setExercises,
    setExerciseProgress,
    setCurrentIndex,
    setTierInfo,
    setCoreBalance,
    setContentLoadingMap,
    setContentErrorMap,
    showExerciseList,
    setShowExerciseList,
  }
}
