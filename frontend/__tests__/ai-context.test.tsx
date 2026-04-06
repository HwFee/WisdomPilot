import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

// ============================================================
// MOCK: react-markdown
// ============================================================
jest.mock('react-markdown', () => {
  return function MockMarkdown({ children }: { children: React.ReactNode }) {
    return <>{children}</>
  }
})
jest.mock('remark-gfm', () => () => {})

// ============================================================
// MOCK: getStoredToken
// ============================================================
jest.mock('@/lib/api', () => ({
  getStoredToken: jest.fn(() => 'fake-test-token'),
}))

// ============================================================
// MOCK: AI API functions
// ============================================================
const mockGetChoiceExplanation = jest.fn()
const mockGetChoiceAnalysis = jest.fn()
const mockGetCodeFeedback = jest.fn()
jest.mock('@/lib/ai-api', () => ({
  getChoiceExplanation: (...args: unknown[]) => mockGetChoiceExplanation(...args),
  getChoiceAnalysis: (...args: unknown[]) => mockGetChoiceAnalysis(...args),
  getCodeFeedback: (...args: unknown[]) => mockGetCodeFeedback(...args),
}))

// ============================================================
// DYNAMIC IMPORT: AIContext
// ============================================================
let AIContextProvider: React.ComponentType<{ children: React.ReactNode }>
let useAIContext: () => ReturnType<typeof import('@/contexts/AIContext').useAIContext>

beforeAll(async () => {
  const mod = await import('@/contexts/AIContext')
  AIContextProvider = mod.AIContextProvider
  useAIContext = mod.useAIContext
})

beforeEach(() => {
  jest.clearAllMocks()
})

// ============================================================
// TEST: useAIContext without provider throws
// ============================================================
it('useAIContext without AIContextProvider throws error', () => {
  const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})
  const TestComponent = () => {
    useAIContext()
    return null
  }
  expect(() => render(<TestComponent />)).toThrow(
    'useAIContext must be used within AIContextProvider'
  )
  consoleError.mockRestore()
})

// ============================================================
// TEST: AIContextProvider initializes with null context
// ============================================================
it('AIContextProvider initializes with null context', () => {
  const DisplayContext = () => {
    const ctx = useAIContext()
    return (
      <span data-testid="context">
        {ctx.currentExercise === null ? 'null' : 'has-value'}
      </span>
    )
  }
  render(
    <AIContextProvider>
      <DisplayContext />
    </AIContextProvider>
  )
  expect(screen.getByTestId('context').textContent).toBe('null')
})

// ============================================================
// TEST: setCurrentExercise updates the context
// ============================================================
it('setCurrentExercise updates current exercise', async () => {
  const DisplayContext = () => {
    const ctx = useAIContext()
    return (
      <div>
        <span data-testid="exercise-type">{(ctx.currentExercise?.type as string) ?? 'none'}</span>
        <button
          onClick={() =>
            ctx.setCurrentExercise({
              type: 'choice',
              chapterId: 1,
              subsectionIndex: 0,
              exerciseId: 1,
              question: 'What is 2+2?',
              options: ['3', '4', '5'],
              selectedAnswer: 0,
              correctAnswer: 1,
            })
          }
        >
          set
        </button>
      </div>
    )
  }

  let utils!: ReturnType<typeof render>
  await act(async () => {
    utils = render(
      <AIContextProvider>
        <DisplayContext />
      </AIContextProvider>
    )
  })

  expect(utils.container.querySelector('[data-testid="exercise-type"]')?.textContent).toBe('none')

  await act(async () => {
    await userEvent.click(screen.getByRole('button', { name: 'set' }))
  })

  expect(screen.getByTestId('exercise-type').textContent).toBe('choice')
})

// ============================================================
// TEST: clearResults resets hint and analysis results
// ============================================================
it('clearResults resets hint result', async () => {
  mockGetChoiceExplanation.mockResolvedValueOnce({ explanation: 'A hint' })

  let utils!: ReturnType<typeof render>
  let ctxRef!: ReturnType<typeof useAIContext>

  const DisplayResults = () => {
    const ctx = useAIContext()
    ctxRef = ctx
    return (
      <div>
        <span data-testid="hint-result">{ctx.hintResult ?? 'none'}</span>
        <button onClick={() => ctx.setCurrentExercise({
          type: 'choice',
          chapterId: 1,
          subsectionIndex: 0,
          exerciseId: 1,
          question: 'What is 2+2?',
          options: ['3', '4', '5'],
          selectedAnswer: 0,
          correctAnswer: 1,
        })}>setCtx</button>
        <button onClick={() => ctx.triggerHint()}>triggerHint</button>
        <button onClick={ctx.clearResults}>clear</button>
      </div>
    )
  }

  await act(async () => {
    utils = render(
      <AIContextProvider>
        <DisplayResults />
      </AIContextProvider>
    )
  })

  await act(async () => {
    await userEvent.click(screen.getByRole('button', { name: 'setCtx' }))
    await ctxRef.triggerHint()
  })

  await waitFor(() => {
    expect(screen.getByTestId('hint-result').textContent).toBe('A hint')
  })

  await act(async () => {
    await userEvent.click(screen.getByRole('button', { name: 'clear' }))
  })

  await waitFor(() => {
    expect(screen.getByTestId('hint-result').textContent).toBe('none')
  })

  await act(async () => {
    utils!.unmount()
  })
})

// ============================================================
// TEST: triggerHint calls getChoiceExplanation and sets hintResult
// ============================================================
it('triggerHint calls getChoiceExplanation and shows result', async () => {
  mockGetChoiceExplanation.mockResolvedValueOnce({ explanation: 'Hint: think about base case' })

  let utils!: ReturnType<typeof render>
  let ctxRef!: ReturnType<typeof useAIContext>

  const DisplayHint = () => {
    const ctx = useAIContext()
    ctxRef = ctx
    return (
      <div>
        <span data-testid="hint-loading">{ctx.hintLoading ? 'loading' : 'idle'}</span>
        <span data-testid="hint-result">{ctx.hintResult ?? 'none'}</span>
        <button onClick={() => ctx.setCurrentExercise({
          type: 'choice',
          chapterId: 1,
          subsectionIndex: 0,
          exerciseId: 1,
          question: 'What is 2+2?',
          options: ['3', '4', '5'],
          selectedAnswer: 0,
          correctAnswer: 1,
        })}>setCtx</button>
        <button onClick={() => ctx.triggerHint()}>triggerHint</button>
      </div>
    )
  }

  await act(async () => {
    utils = render(
      <AIContextProvider>
        <DisplayHint />
      </AIContextProvider>
    )
  })

  await act(async () => {
    await userEvent.click(screen.getByRole('button', { name: 'setCtx' }))
    await ctxRef.triggerHint()
  })

  await waitFor(() => {
    expect(screen.getByTestId('hint-result').textContent).toBe('Hint: think about base case')
  })
  expect(screen.getByTestId('hint-loading').textContent).toBe('idle')
  expect(mockGetChoiceExplanation).toHaveBeenCalledWith('fake-test-token', expect.objectContaining({
    question: 'What is 2+2?',
    options: ['3', '4', '5'],
    user_selected_index: 0,
    correct_index: 1,
  }))

  await act(async () => { utils!.unmount() })
})

// ============================================================
// TEST: triggerHint sets error message on failure
// ============================================================
it('triggerHint sets error message on API failure', async () => {
  mockGetChoiceExplanation.mockRejectedValueOnce(new Error('Network error'))

  let utils!: ReturnType<typeof render>
  let ctxRef!: ReturnType<typeof useAIContext>

  const DisplayHint = () => {
    const ctx = useAIContext()
    ctxRef = ctx
    return (
      <div>
        <span data-testid="hint-loading">{ctx.hintLoading ? 'loading' : 'idle'}</span>
        <span data-testid="hint-result">{ctx.hintResult ?? 'none'}</span>
        <button onClick={() => ctx.setCurrentExercise({
          type: 'choice',
          chapterId: 1,
          subsectionIndex: 0,
          exerciseId: 1,
          question: 'What is 2+2?',
          options: ['3', '4', '5'],
          selectedAnswer: 0,
          correctAnswer: 1,
        })}>setCtx</button>
        <button onClick={() => ctx.triggerHint()}>triggerHint</button>
      </div>
    )
  }

  await act(async () => {
    utils = render(
      <AIContextProvider>
        <DisplayHint />
      </AIContextProvider>
    )
  })

  const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})
  await act(async () => {
    await userEvent.click(screen.getByRole('button', { name: 'setCtx' }))
    await ctxRef.triggerHint()
  })
  consoleError.mockRestore()

  await waitFor(() => {
    expect(screen.getByTestId('hint-result').textContent).toBe('获取 AI 提示失败，请重试。')
  })
  expect(screen.getByTestId('hint-loading').textContent).toBe('idle')

  await act(async () => { utils!.unmount() })
})

// ============================================================
// TEST: triggerAnalysis calls getChoiceAnalysis and sets analysisResult
// ============================================================
it('triggerAnalysis calls getChoiceAnalysis and shows analysis result', async () => {
  mockGetChoiceAnalysis.mockResolvedValueOnce({
    analysis: 'Your understanding is correct but check edge cases',
    is_correct: false,
  })

  let utils!: ReturnType<typeof render>
  let ctxRef!: ReturnType<typeof useAIContext>

  const DisplayAnalysis = () => {
    const ctx = useAIContext()
    ctxRef = ctx
    return (
      <div>
        <span data-testid="analysis-loading">{ctx.analysisLoading ? 'loading' : 'idle'}</span>
        <span data-testid="analysis-result">{ctx.analysisResult?.analysis ?? 'none'}</span>
        <span data-testid="analysis-correct">{String(ctx.analysisResult?.is_correct ?? 'none')}</span>
        <button onClick={() => ctx.setCurrentExercise({
          type: 'choice',
          chapterId: 1,
          subsectionIndex: 0,
          exerciseId: 1,
          question: 'What is 2+2?',
          options: ['3', '4', '5'],
          selectedAnswer: 0,
          correctAnswer: 1,
        })}>setCtx</button>
        <button onClick={() => ctx.triggerAnalysis()}>triggerAnalysis</button>
      </div>
    )
  }

  await act(async () => {
    utils = render(
      <AIContextProvider>
        <DisplayAnalysis />
      </AIContextProvider>
    )
  })

  await act(async () => {
    await userEvent.click(screen.getByRole('button', { name: 'setCtx' }))
    await ctxRef.triggerAnalysis()
  })

  await waitFor(() => {
    expect(screen.getByTestId('analysis-result').textContent).toBe('Your understanding is correct but check edge cases')
  })
  expect(screen.getByTestId('analysis-correct').textContent).toBe('false')
  expect(mockGetChoiceAnalysis).toHaveBeenCalledWith('fake-test-token', expect.objectContaining({
    question_text: 'What is 2+2?',
    options: ['3', '4', '5'],
    user_selected: 0,
    correct_answer: 1,
  }))

  await act(async () => { utils!.unmount() })
})

// ============================================================
// TEST: triggerFeedback calls getCodeFeedback and sets feedbackResult
// ============================================================
it('triggerFeedback calls getCodeFeedback and shows diagnosis', async () => {
  mockGetCodeFeedback.mockResolvedValueOnce({
    diagnosis: 'Missing base case in recursion',
    suggestions: 'Add if n <= 1: return n',
    optimized_code: 'def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)',
  })

  let ctxRef!: ReturnType<typeof useAIContext>

  const DisplayFeedback = () => {
    const ctx = useAIContext()
    ctxRef = ctx
    return (
      <div>
        <span data-testid="feedback-loading">{ctx.feedbackLoading ? 'loading' : 'idle'}</span>
        <span data-testid="feedback-diagnosis">{ctx.feedbackResult?.diagnosis ?? 'none'}</span>
        <span data-testid="feedback-suggestions">{ctx.feedbackResult?.suggestions ?? 'none'}</span>
        <button onClick={() => ctx.setCurrentExercise({
          type: 'programming',
          chapterId: 1,
          subsectionIndex: 0,
          exerciseId: 1,
          code: 'def fib(n): return n',
          language: 'python',
          exerciseDescription: 'Implement fibonacci',
        })}>setCtx</button>
        <button onClick={() => ctx.triggerFeedback()}>triggerFeedback</button>
      </div>
    )
  }

  let utils!: ReturnType<typeof render>

  await act(async () => {
    utils = render(
      <AIContextProvider>
        <DisplayFeedback />
      </AIContextProvider>
    )
  })

  await act(async () => {
    await userEvent.click(screen.getByRole('button', { name: 'setCtx' }))
  })

  await act(async () => {
    // Call triggerFeedback directly and await it so act() waits for the async completion
    const feedbackPromise = ctxRef.triggerFeedback()
    await feedbackPromise
  })

  await waitFor(() => {
    expect(screen.getByTestId('feedback-diagnosis').textContent).toBe('Missing base case in recursion')
  })
  expect(screen.getByTestId('feedback-loading').textContent).toBe('idle')
  expect(screen.getByTestId('feedback-suggestions').textContent).toBe('Add if n <= 1: return n')

  await act(async () => { utils!.unmount() })
})
