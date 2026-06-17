import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { useChallengeSubmit } from '@/app/arena/use-challenge-submit'
import type { ChallengeSubmitDeps } from '@/app/arena/use-challenge-submit'
import type { Exercise, ExerciseProgress } from '@/app/arena/types'
import { LANGUAGE_MAP } from '@/app/arena/types'

const mockGetStoredToken = jest.fn(() => 'token-1')
const mockSubmitChallengeExercise = jest.fn()
const mockAppendChallengeExercises = jest.fn()
const mockGetChallengeProgress = jest.fn()
const mockExecuteCodeBatch = jest.fn()

jest.mock('@/lib/api', () => ({
  TIER_NAMES: { bronze: '青铜', silver: '白银', gold: '黄金' },
  getStoredToken: () => mockGetStoredToken(),
  submitChallengeExercise: (...args: unknown[]) => mockSubmitChallengeExercise(...args),
  appendChallengeExercises: (...args: unknown[]) => mockAppendChallengeExercises(...args),
  getChallengeProgress: (...args: unknown[]) => mockGetChallengeProgress(...args),
}))

jest.mock('@/lib/api/code', () => ({
  executeCodeBatch: (...args: unknown[]) => mockExecuteCodeBatch(...args),
}))

jest.mock('@/lib/codeTemplates', () => ({
  getTemplate: (lang: string) => `// ${lang} template`,
}))

const SAMPLE_EXERCISE: Exercise = {
  id: 101,
  type: 'programming',
  difficulty: 2,
  content: {
    title: 'Test Exercise',
    description: 'A test exercise',
    code_template: '// python template',
    sample_input: '1 2',
    sample_output: '3',
    samples: [{ input: '1 2', output: '3' }],
  },
  knowledge_points: ['basics'],
  test_cases: [
    { input: '1 2', output: '3' },
    { input: '4 5', output: '9' },
  ],
}

const SAMPLE_PROGRESS: ExerciseProgress[] = [
  {
    exercise_id: 101,
    exercise_index: 0,
    is_completed: false,
    is_correct: false,
    is_unlocked: true,
    saved_code: '',
    current_language: 'python',
    title: 'Test Exercise',
    difficulty: 2,
  },
  {
    exercise_id: 102,
    exercise_index: 1,
    is_completed: false,
    is_correct: false,
    is_unlocked: false,
    saved_code: '',
    current_language: 'python',
    title: 'Next Exercise',
    difficulty: 2,
  },
]

function SubmitButton(deps: ChallengeSubmitDeps) {
  const handleSubmit = useChallengeSubmit(deps)
  return <button onClick={handleSubmit}>Submit</button>
}

function createDeps(overrides: Partial<ChallengeSubmitDeps> = {}): ChallengeSubmitDeps {
  return {
    exercises: [SAMPLE_EXERCISE],
    exerciseProgress: SAMPLE_PROGRESS,
    currentExercise: SAMPLE_EXERCISE,
    language: 'python',
    code: 'print("hello")',
    isSubmitting: false,
    savedCodesRef: { current: {} } as React.MutableRefObject<Record<number, Record<string, string>>>,
    currentDifficultyRef: { current: 2 } as React.MutableRefObject<number>,
    setIsSubmitting: jest.fn(),
    setTestResults: jest.fn(),
    setRightPanelTab: jest.fn(),
    setFeedbackState: jest.fn(),
    setModalResult: jest.fn(),
    setShowResultModal: jest.fn(),
    setTierInfo: jest.fn(),
    setExercises: jest.fn(),
    setExerciseProgress: jest.fn(),
    push: jest.fn(),
    LANGUAGE_MAP,
    ...overrides,
  }
}

describe('useChallengeSubmit', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetStoredToken.mockReturnValue('token-1')
    mockAppendChallengeExercises.mockResolvedValue({ new_exercise_ids: [] })
    mockGetChallengeProgress.mockResolvedValue({ exercises: [] })
  })

  it('should submit successfully and show correct result', async () => {
    const deps = createDeps()

    mockExecuteCodeBatch.mockResolvedValue({
      token: 'batch-token',
      status: 'completed',
      status_id: 3,
      passed_count: 2,
      total_count: 2,
      results: [
        { passed: true, expected: '3', actual: '3', message: '' },
        { passed: true, expected: '9', actual: '9', message: '' },
      ],
    })

    const backendResults = [
      { passed: true, input: 'hidden', expected: '10', actual: '10', message: '' },
      { passed: true, input: 'hidden-2', expected: '11', actual: '11', message: '' },
      { passed: true, input: 'hidden-3', expected: '12', actual: '12', message: '' },
    ]

    mockSubmitChallengeExercise.mockResolvedValue({
      is_correct: true,
      test_results: backendResults,
      stars_earned: 1,
      cores_earned: 5,
      next_unlocked: true,
      added_to_wrong_book: false,
      tier_changed: false,
      new_tier: null,
      new_sub_tier: null,
      new_stars: 0,
      promoted: false,
      demoted: false,
      first_time_correct: true,
      first_time_wrong: false,
    })

    render(<SubmitButton {...deps} />)
    await userEvent.click(screen.getByText('Submit'))

    await waitFor(() => {
      expect(mockExecuteCodeBatch).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 'print("hello")',
          language_id: 71,
          test_cases: [
            { input: '1 2', expected_output: '3' },
            { input: '4 5', expected_output: '9' },
          ],
        }),
        'token-1',
      )
    })

    await waitFor(() => {
      expect(mockSubmitChallengeExercise).toHaveBeenCalledWith(
        expect.objectContaining({
          exercise_id: 101,
          code: 'print("hello")',
          language: 'python',
        }),
        'token-1',
      )
    })

    expect(deps.setTestResults).toHaveBeenCalledWith([
      { passed: true, input: '1 2', expected: '3', actual: '3', message: '' },
      { passed: true, input: '4 5', expected: '9', actual: '9', message: '' },
    ])
    expect(deps.setTestResults).toHaveBeenLastCalledWith(backendResults)
    expect(deps.setFeedbackState).toHaveBeenCalledWith('correct')
    expect(deps.setShowResultModal).toHaveBeenCalledWith(true)
    expect(deps.setModalResult).toHaveBeenCalledWith(
      expect.objectContaining({
        isCorrect: true,
        passedCount: 3,
        totalCount: 3,
        starsEarned: 1,
        firstTimeCorrect: true,
      }),
    )
    expect(deps.setExerciseProgress).toHaveBeenCalled()
  })

  it('should handle exercise with no test cases', async () => {
    const exerciseNoTests: Exercise = {
      ...SAMPLE_EXERCISE,
      test_cases: [],
    }
    const deps = createDeps({ currentExercise: exerciseNoTests })

    render(<SubmitButton {...deps} />)
    await userEvent.click(screen.getByText('Submit'))

    await waitFor(() => {
      expect(deps.setTestResults).toHaveBeenCalledWith([
        expect.objectContaining({ message: '该题目暂无测试用例' }),
      ])
    })

    expect(deps.setFeedbackState).toHaveBeenCalledWith('wrong')
    expect(mockExecuteCodeBatch).not.toHaveBeenCalled()
    expect(mockSubmitChallengeExercise).not.toHaveBeenCalled()
  })

  it('should let backend-authoritative result override frontend batch result', async () => {
    const deps = createDeps()

    mockExecuteCodeBatch.mockResolvedValue({
      token: 'batch-token',
      status: 'completed',
      status_id: 3,
      passed_count: 2,
      total_count: 2,
      results: [
        { passed: true, expected: '3', actual: '3', message: '' },
        { passed: true, expected: '9', actual: '9', message: '' },
      ],
    })

    mockSubmitChallengeExercise.mockResolvedValue({
      is_correct: false,
      test_results: [],
      stars_earned: 0,
      cores_earned: 0,
      next_unlocked: false,
      added_to_wrong_book: true,
      tier_changed: false,
      new_tier: null,
      new_sub_tier: null,
      new_stars: 0,
      promoted: false,
      demoted: false,
      first_time_correct: false,
      first_time_wrong: true,
    })

    render(<SubmitButton {...deps} />)
    await userEvent.click(screen.getByText('Submit'))

    await waitFor(() => {
      expect(deps.setFeedbackState).toHaveBeenCalledWith('correct')
    })

    await waitFor(() => {
      expect(deps.setFeedbackState).toHaveBeenCalledWith('wrong')
    })

    expect(deps.setShowResultModal).not.toHaveBeenCalled()
    expect(deps.setModalResult).not.toHaveBeenCalled()
  })
})
