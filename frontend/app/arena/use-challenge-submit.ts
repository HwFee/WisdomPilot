'use client'

import { useCallback } from 'react'
import {
  TIER_NAMES,
  getStoredToken,
  appendChallengeExercises,
  getChallengeProgress,
  submitChallengeExercise,
} from '@/lib/api'
import { executeCodeBatch } from '@/lib/api/code'
import { getTemplate } from '@/lib/codeTemplates'
import type {
  Exercise,
  ExerciseProgress,
  ProgressExercise,
  TestCaseResult,
  LanguageConfig,
} from './types'

type TierInfo = {
  tier: string
  sub_tier: number
  stars: number
  full_name: string
} | null

type ModalResultShape = {
  isCorrect: boolean
  passedCount: number
  totalCount: number
  starsEarned: number
  promoted: boolean
  demoted: boolean
  firstTimeCorrect: boolean
  firstTimeWrong: boolean
}

const REMAINING_THRESHOLD = 2
const APPEND_COUNT = 5
const NO_TEST_CASES_MESSAGE = '该题目暂无测试用例'
const SUBMIT_FAILED_MESSAGE = '提交失败，请重试'
const ROMAN_SUB_TIER = ['I', 'II', 'III', 'IV', 'V'] as const

function buildTestCasesForApi(testCases: Array<{ input?: string; output?: string }>) {
  return testCases.map((tc) => ({
    input: tc.input || '',
    expected_output: tc.output || '',
  }))
}

function mapBatchResultsToUiResults(
  batchResults: Array<{ passed: boolean; expected: string; actual: string; message?: string }>,
  testCases: Array<{ input?: string }>,
): TestCaseResult[] {
  return batchResults.map((result, index) => ({
    passed: result.passed,
    input: testCases[index]?.input || '',
    expected: result.expected,
    actual: result.actual,
    message: result.message,
  }))
}

function resolveLanguageId(language: string, languageMap: Record<string, LanguageConfig>): number {
  return languageMap[language]?.id || 71
}

function buildTierInfo(
  newTier: string,
  newSubTier: number | null,
  newStars: number,
): TierInfo {
  const subTierRoman = newSubTier ? ROMAN_SUB_TIER[newSubTier - 1] : ''
  return {
    tier: newTier,
    sub_tier: newSubTier || 4,
    stars: newStars,
    full_name: `${TIER_NAMES[newTier] || newTier}${subTierRoman}`,
  }
}

function updateProgressAfterSubmit(
  prev: ExerciseProgress[],
  exerciseId: number,
  isCorrect: boolean,
): ExerciseProgress[] {
  const updated = [...prev]
  const idx = updated.findIndex((p) => p.exercise_id === exerciseId)
  if (idx < 0) return updated

  updated[idx] = {
    ...updated[idx],
    is_completed: true,
    is_correct: isCorrect,
    is_unlocked: true,
  }

  const currentExerciseIndex = updated[idx].exercise_index
  const nextIdx = updated.findIndex(
    (p) => p.exercise_index === currentExerciseIndex + 1,
  )
  if (nextIdx !== -1 && !updated[nextIdx].is_unlocked) {
    updated[nextIdx] = { ...updated[nextIdx], is_unlocked: true }
  }

  return updated
}

function buildNoTestCasesResult(): TestCaseResult[] {
  return [{
    passed: false,
    input: '',
    expected: '',
    actual: '',
    message: NO_TEST_CASES_MESSAGE,
  }]
}

function buildSubmitFailedResult(): TestCaseResult[] {
  return [{
    passed: false,
    input: '',
    expected: '',
    actual: '',
    message: SUBMIT_FAILED_MESSAGE,
  }]
}

async function appendExercisesIfNeeded(
  exerciseProgress: ExerciseProgress[],
  currentExerciseId: number,
  exercises: Exercise[],
  currentDifficulty: number,
  token: string,
  setExercises: (updater: (prev: Exercise[]) => Exercise[]) => void,
  setExerciseProgress: (updater: (prev: ExerciseProgress[]) => ExerciseProgress[]) => void,
  savedCodesRef: React.MutableRefObject<Record<number, Record<string, string>>>,
) {
  const currentExerciseIdx = exerciseProgress.findIndex(
    (p) => p.exercise_id === currentExerciseId,
  )
  const remainingUncompleted = exerciseProgress
    .slice(currentExerciseIdx + 1)
    .filter((p) => !p.is_completed).length

  if (remainingUncompleted > REMAINING_THRESHOLD) return

  try {
    const appendResult = await appendChallengeExercises(
      { count: APPEND_COUNT, difficulty_level: currentDifficulty },
      token,
    )
    if (appendResult.new_exercise_ids.length === 0) return

    const newProgressData = await getChallengeProgress(token, true)

    const existingIds = new Set(exercises.map((e) => e.id))
    const newExercises: Exercise[] = []
    for (const ex of newProgressData.exercises as ProgressExercise[]) {
      if (!existingIds.has(ex.exercise_id)) {
        newExercises.push({
          id: ex.exercise_id,
          type: 'programming' as const,
          difficulty: ex.difficulty || 1,
          content: {
            title: ex.title || `题目 ${ex.exercise_index + 1}`,
            description: '',
            code_template: getTemplate('python'),
            sample_input: '',
            sample_output: '',
            samples: [],
          },
          knowledge_points: [],
          test_cases: [],
        })
      }
    }

    setExercises((prev) => [...prev, ...newExercises])
    setExerciseProgress((prev) => [
      ...prev,
      ...newProgressData.exercises.filter(
        (ex: ExerciseProgress) =>
          !prev.find((p) => p.exercise_id === ex.exercise_id),
      ),
    ])

    const newSavedCodes: Record<number, Record<string, string>> = {}
    newProgressData.exercises.forEach((ex: ExerciseProgress) => {
      if (!savedCodesRef.current[ex.exercise_id]) {
        newSavedCodes[ex.exercise_id] = {
          python: ex.saved_code || getTemplate('python'),
        }
      }
    })
    savedCodesRef.current = { ...savedCodesRef.current, ...newSavedCodes }
  } catch (error) {
    console.error('[挑战之路] 追加题目失败:', error)
  }
}

export type ChallengeSubmitDeps = {
  exercises: Exercise[]
  exerciseProgress: ExerciseProgress[]
  currentExercise: Exercise | undefined
  language: string
  code: string
  isSubmitting: boolean
  savedCodesRef: React.MutableRefObject<Record<number, Record<string, string>>>
  currentDifficultyRef: React.MutableRefObject<number>
  setIsSubmitting: (v: boolean) => void
  setTestResults: (v: TestCaseResult[]) => void
  setRightPanelTab: (v: 'code' | 'test' | 'output') => void
  setFeedbackState: (v: 'idle' | 'correct' | 'wrong') => void
  setModalResult: (v: ModalResultShape) => void
  setShowResultModal: (v: boolean) => void
  setTierInfo: (v: TierInfo) => void
  setExercises: (updater: (prev: Exercise[]) => Exercise[]) => void
  setExerciseProgress: (updater: (prev: ExerciseProgress[]) => ExerciseProgress[]) => void
  push: (url: string) => void
  LANGUAGE_MAP: Record<string, LanguageConfig>
}

export function useChallengeSubmit(deps: ChallengeSubmitDeps) {
  const {
    currentExercise,
    exercises,
    exerciseProgress,
    code,
    language,
    isSubmitting,
    setIsSubmitting,
    setTestResults,
    setRightPanelTab,
    setFeedbackState,
    setModalResult,
    setShowResultModal,
    setTierInfo,
    setExercises,
    setExerciseProgress,
    savedCodesRef,
    currentDifficultyRef,
    push,
    LANGUAGE_MAP,
  } = deps

  return useCallback(async () => {
    if (!currentExercise || isSubmitting) return

    setIsSubmitting(true)
    setTestResults([])
    setRightPanelTab('output')

    try {
      const token = getStoredToken()
      if (!token) {
        push('/login')
        return
      }

      const testCases = currentExercise.test_cases || []
      if (testCases.length === 0) {
        setTestResults(buildNoTestCasesResult())
        setFeedbackState('wrong')
        setIsSubmitting(false)
        return
      }

      const testCasesForApi = buildTestCasesForApi(testCases)
      const languageId = resolveLanguageId(language, LANGUAGE_MAP)

      const batchResult = await executeCodeBatch(
        { code, language_id: languageId, test_cases: testCasesForApi },
        token,
      )

      const results = mapBatchResultsToUiResults(batchResult.results, testCases)
      setTestResults(results)

      const allFrontendPassed = batchResult.passed_count === batchResult.total_count
      setFeedbackState(allFrontendPassed ? 'correct' : 'wrong')

      const submitResult = await submitChallengeExercise(
        {
          exercise_id: currentExercise.id,
          code,
          language,
          test_results: results,
        },
        token,
      )

      const finalIsCorrect = submitResult.is_correct
      setFeedbackState(finalIsCorrect ? 'correct' : 'wrong')

      if (submitResult.tier_changed && submitResult.new_tier) {
        setTierInfo(buildTierInfo(
          submitResult.new_tier,
          submitResult.new_sub_tier,
          submitResult.new_stars,
        ))
      }

      setExerciseProgress((prev) =>
        updateProgressAfterSubmit(prev, currentExercise.id, finalIsCorrect),
      )

      savedCodesRef.current = {
        ...savedCodesRef.current,
        [currentExercise.id]: {
          ...savedCodesRef.current[currentExercise.id],
          [language]: code,
        },
      }

      if (finalIsCorrect) {
        setModalResult({
          isCorrect: true,
          passedCount: batchResult.passed_count,
          totalCount: batchResult.total_count,
          starsEarned: submitResult.stars_earned,
          promoted: submitResult.promoted,
          demoted: submitResult.demoted,
          firstTimeCorrect: submitResult.first_time_correct,
          firstTimeWrong: submitResult.first_time_wrong,
        })
        setShowResultModal(true)
      }

      await appendExercisesIfNeeded(
        exerciseProgress,
        currentExercise.id,
        exercises,
        currentDifficultyRef.current,
        token,
        setExercises,
        setExerciseProgress,
        savedCodesRef,
      )
    } catch (error) {
      console.error('Failed to submit:', error)
      setFeedbackState('wrong')
      setTestResults(buildSubmitFailedResult())
    } finally {
      setIsSubmitting(false)
    }
  }, [
    currentExercise,
    exercises,
    exerciseProgress,
    code,
    language,
    isSubmitting,
    setIsSubmitting,
    setTestResults,
    setRightPanelTab,
    setFeedbackState,
    setModalResult,
    setShowResultModal,
    setTierInfo,
    setExercises,
    setExerciseProgress,
    savedCodesRef,
    currentDifficultyRef,
    push,
    LANGUAGE_MAP,
  ])
}
