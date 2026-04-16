'use client'

import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState, useCallback, useRef } from 'react'
import {
  X, CheckCircle, XCircle, ArrowRight, RotateCcw, Zap,
  ChevronRight, ChevronLeft, Loader2, Code2, Terminal, Send
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import {
  getArenaProfile,
  startInfiniteSession,
  getInfiniteProgress,
  submitInfiniteExercise,
  saveInfiniteCode,
  switchInfiniteExercise,
  exitInfiniteSession,
  TIER_ICONS, TIER_NAMES
} from '@/lib/api'
import { executeCode, executeCodeBatch } from '@/lib/api/code'
import { CodeEditorPanel } from '@/components/exercise/CodeEditorPanel'
import { SampleIOCard } from '@/components/exercise/SampleIOCard'
import { CustomTestInput, TestOutputDisplay } from '@/components/exercise/CustomTestInput'
import { LuoguTestCaseTable, LuoguTestCasesSummary } from '@/components/exercise/LuoguTestCaseTable'
import { getTemplate } from '@/lib/codeTemplates'
import type { ArenaProfileResponse, ChallengeSessionResponse, ChallengeExercise } from '@/types/api'

// ========================================
// Types
// ========================================

interface Exercise {
  id: number
  type: 'choice' | 'programming' | 'fill_blank'
  difficulty: number
  content: {
    text?: string
    title?: string
    description?: string
    options?: string[]
    code_template?: string
    input_format?: string
    output_format?: string
    sample_input?: string
    sample_output?: string
    time_limit?: number
    memory_limit?: number
    samples?: Array<{ input: string; output: string }>
  }
  knowledge_points: string[]
  hints?: string[]
  test_cases?: Array<{input: string, output: string, name?: string}>
  solution?: {
    answer?: string
    explanation?: string
  }
}

interface TestCaseResult {
  passed: boolean
  input: string
  expected: string
  actual: string
  time?: number
  memory?: number
  message?: string
}

interface ExerciseProgress {
  exercise_id: number
  exercise_index: number
  is_completed: boolean
  is_correct: boolean
  is_unlocked: boolean
  saved_code: string
  current_language: string
  title: string
  difficulty: number
}

type FeedbackState = 'idle' | 'correct' | 'wrong'
type RightPanelTab = 'code' | 'test' | 'output'

// ========================================
// Language Configuration
// ========================================

interface LanguageConfig {
  id: number
  name: string
  monaco: string
}

const LANGUAGE_MAP: Record<string, LanguageConfig> = {
  c: { id: 50, name: 'C', monaco: 'c' },
  cpp: { id: 54, name: 'C++', monaco: 'cpp' },
  python: { id: 71, name: 'Python', monaco: 'python' },
  java: { id: 62, name: 'Java', monaco: 'java' },
  rust: { id: 73, name: 'Rust', monaco: 'rust' },
}

const LANGUAGE_OPTIONS = Object.entries(LANGUAGE_MAP).map(([key, config]) => ({
  key,
  ...config
}))

// ========================================
// Result Modal Component
// ========================================

interface ResultModalProps {
  isCorrect: boolean
  passedCount: number
  totalCount: number
  xpEarned: number
  onStay: () => void
  onNext: () => void
  canGoNext: boolean
}

function ResultModal({ isCorrect, passedCount, totalCount, xpEarned, onStay, onNext, canGoNext }: ResultModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className={`bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 transform transition-all ${
        isCorrect ? 'border-2 border-[#52C41A]' : 'border-2 border-[#E74C3C]'
      }`}>
        <div className="text-center">
          {isCorrect ? (
            <>
              <CheckCircle className="w-20 h-20 text-[#52C41A] mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-[#52C41A] mb-2">太棒了！全部通过</h2>
              <p className="text-[#606266] mb-6">
                +{xpEarned} XP · 继续挑战下一题
              </p>
            </>
          ) : (
            <>
              <XCircle className="w-20 h-20 text-[#E74C3C] mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-[#E74C3C] mb-2">答案错误</h2>
              <p className="text-[#606266] mb-6">
                通过 {passedCount}/{totalCount} 个测试点
              </p>
            </>
          )}

          <div className="flex gap-3 justify-center">
            <button
              onClick={onStay}
              className="px-6 py-3 bg-white border border-[#E4E7ED] rounded-xl font-medium text-[#303133] hover:bg-[#F5F7FA] transition-colors"
            >
              留在本题
            </button>
            {canGoNext && (
              <button
                onClick={onNext}
                className="px-6 py-3 bg-gradient-to-r from-[#3498DB] to-[#2980B9] text-white rounded-xl font-medium hover:shadow-lg transition-all flex items-center gap-2"
              >
                下一题
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ========================================
// Exercise Navigation Component
// ========================================

interface ExerciseNavigationProps {
  exercises: ExerciseProgress[]
  currentIndex: number
  onSwitch: (index: number) => void
}

function ExerciseNavigation({ exercises, currentIndex, onSwitch }: ExerciseNavigationProps) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {exercises.map((ex, index) => (
        <button
          key={ex.exercise_id}
          onClick={() => ex.is_unlocked && onSwitch(index)}
          disabled={!ex.is_unlocked}
          className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${
            index === currentIndex
              ? 'bg-[#3498DB] text-white'
              : ex.is_correct
              ? 'bg-[#52C41A]/20 text-[#52C41A] border border-[#52C41A]/30'
              : ex.is_completed
              ? 'bg-[#E74C3C]/20 text-[#E74C3C] border border-[#E74C3C]/30'
              : ex.is_unlocked
              ? 'bg-white text-[#606266] border border-[#E4E7ED] hover:border-[#3498DB]'
              : 'bg-[#F5F7FA] text-[#C0C4CC] border border-[#E4E7ED] cursor-not-allowed'
          }`}
        >
          {ex.is_correct ? '✓' : ex.is_completed ? '✗' : index + 1}
        </button>
      ))}
    </div>
  )
}

// ========================================
// Main Component
// ========================================

export default function ArenaPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const courseId = parseInt(params.id as string)
  const difficultyFromDashboard = searchParams.get('difficulty')

  // Arena state
  const [profile, setProfile] = useState<ArenaProfileResponse | null>(null)
  const [session, setSession] = useState<ChallengeSessionResponse | null>(null)
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [exerciseProgress, setExerciseProgress] = useState<ExerciseProgress[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)

  // Code state - saved codes per exercise, per language
  const [savedCodes, setSavedCodes] = useState<Record<number, Record<string, string>>>({})
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState<string>('python')
  const [feedbackState, setFeedbackState] = useState<FeedbackState>('idle')

  // Right panel state
  const [rightPanelTab, setRightPanelTab] = useState<RightPanelTab>('code')
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

  // Result modal state
  const [showResultModal, setShowResultModal] = useState(false)
  const [modalResult, setModalResult] = useState<{ isCorrect: boolean; passedCount: number; totalCount: number; xpEarned: number } | null>(null)

  // XP tracking
  const [xpEarned, setXpEarned] = useState(0)

  // Refs
  const codeRef = useRef(code)
  codeRef.current = code
  const mountedRef = useRef(true)

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      // Save progress on exit
      handleExitSave()
    }
  }, [])

  // ========================================
  // Data Fetching
  // ========================================

  const initChallenge = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    const difficulty = difficultyFromDashboard ? parseInt(difficultyFromDashboard) : 3

    try {
      setLoading(true)

      const profileData = await getArenaProfile(courseId, token)
      if (!mountedRef.current) return
      setProfile(profileData)

      const sessionData = await startInfiniteSession(courseId, {
        difficulty_level: difficulty,
        initial_count: 10
      }, token)

      if (!mountedRef.current) return

      setSession(sessionData)
      setCurrentIndex(0)

      // Convert session exercises to our format
      const exerciseList: Exercise[] = sessionData.exercises.map((ex: ChallengeExercise) => {
        const testCases = ex.test_cases || []
        const samples = ex.content?.samples || []
        const sampleInput = samples[0]?.input || testCases[0]?.input || ''
        const sampleOutput = samples[0]?.output || testCases[0]?.output || ''
        return {
          id: ex.id,
          type: 'programming' as const,
          difficulty: ex.difficulty || difficulty,
          content: {
            text: ex.content?.text || ex.title,
            title: ex.title,
            description: ex.content?.description || ex.content?.text || ex.title,
            code_template: ex.content?.code_template || getTemplate('python'),
            sample_input: sampleInput,
            sample_output: sampleOutput,
            samples: samples,
          },
          knowledge_points: ex.knowledge_points || [],
          test_cases: testCases.map((tc) => ({
            input: tc.input || '',
            output: tc.output || '',
          })),
        }
      })

      setExercises(exerciseList)

      // Initialize progress - first exercise is unlocked
      const initialProgress: ExerciseProgress[] = exerciseList.map((ex, index) => ({
        exercise_id: ex.id,
        exercise_index: index,
        is_completed: false,
        is_correct: false,
        is_unlocked: index === 0,
        saved_code: '',
        current_language: 'python',
        title: ex.content.title || `题目 ${index + 1}`,
        difficulty: ex.difficulty,
      }))
      setExerciseProgress(initialProgress)

      // Initialize saved codes
      const initialCodes: Record<number, Record<string, string>> = {}
      exerciseList.forEach(ex => {
        initialCodes[ex.id] = { python: ex.content.code_template || getTemplate('python') }
      })
      setSavedCodes(initialCodes)

      if (exerciseList.length > 0) {
        setCode(exerciseList[0].content.code_template || getTemplate('python'))
      }

      // Set language based on preference
      const savedLanguage = localStorage.getItem('preferred_language')
      if (savedLanguage && LANGUAGE_MAP[savedLanguage]) {
        setLanguage(savedLanguage)
      }

    } catch (error) {
      if (mountedRef.current) {
        console.error('Failed to initialize challenge:', error)
        router.push('/dashboard')
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }, [courseId, router, difficultyFromDashboard])

  useEffect(() => {
    initChallenge()
  }, [initChallenge])

  // ========================================
  // Language helpers
  // ========================================

  const getLanguageId = () => LANGUAGE_MAP[language]?.id || 71

  const handleLanguageChange = (newLang: string) => {
    if (newLang === language) return

    const currentExercise = exercises[currentIndex]
    if (!currentExercise) return

    // Save current code for current language
    setSavedCodes(prev => ({
      ...prev,
      [currentExercise.id]: {
        ...prev[currentExercise.id],
        [language]: codeRef.current
      }
    }))

    // Switch language
    setLanguage(newLang)
    localStorage.setItem('preferred_language', newLang)

    // Restore code for new language or use template
    const savedCodeForNewLang = savedCodes[currentExercise.id]?.[newLang]
    if (savedCodeForNewLang) {
      setCode(savedCodeForNewLang)
    } else {
      setCode(getTemplate(newLang))
    }

    // Save to backend
    const token = localStorage.getItem('token')
    if (token && session) {
      saveInfiniteCode(courseId, session.session_id, {
        exercise_id: currentExercise.id,
        code: codeRef.current,
        language: language
      }, token).catch(console.error)
    }
  }

  // ========================================
  // Test execution
  // ========================================

  const handleCustomRun = async (input: string, isFromSample: boolean = false) => {
    if (!code || isCustomRunning) return

    setIsCustomRunning(true)
    setCustomTestOutput(null)
    if (isFromSample) {
      setRightPanelTab('test')
    }

    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const result = await executeCode({
        code: code,
        language_id: getLanguageId(),
        stdin: input,
      }, token)

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
  }

  const handleSampleRun = async (input: string, expectedOutput?: string) => {
    setCustomTestInput(input)

    if (!code || isCustomRunning) return

    setIsCustomRunning(true)
    setCustomTestOutput(null)
    setRightPanelTab('test')

    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const result = await executeCode({
        code: code,
        language_id: getLanguageId(),
        stdin: input,
      }, token)

      const output = (result.stdout || '').trim()
      const expected = (expectedOutput || '').trim()
      const passed = output === expected

      setCustomTestOutput({
        output: output,
        expected: expected,
        passed: passed,
        error: result.stderr || result.compile_output,
      })
    } catch (error) {
      console.error('Sample run failed:', error)
      setCustomTestOutput({ error: '运行失败，请重试' })
    } finally {
      setIsCustomRunning(false)
    }
  }

  // ========================================
  // Submit
  // ========================================

  const handleSubmit = async () => {
    if (!exercises[currentIndex] || isSubmitting) return

    const currentExercise = exercises[currentIndex]

    setIsSubmitting(true)
    setTestResults([])
    setRightPanelTab('output')

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        router.push('/login')
        return
      }

      const testCases = currentExercise.test_cases || []

      if (testCases.length === 0) {
        setTestResults([{
          passed: false,
          input: '',
          expected: '',
          actual: '',
          message: '该题目暂无测试用例'
        }])
        setFeedbackState('wrong')
        setIsSubmitting(false)
        return
      }

      const testCasesForApi = testCases.map(tc => ({
        input: tc.input || '',
        expected_output: tc.output || ''
      }))

      const batchResult = await executeCodeBatch({
        code: code,
        language_id: getLanguageId(),
        test_cases: testCasesForApi
      }, token)

      const results: TestCaseResult[] = batchResult.results.map((r, i) => ({
        passed: r.passed,
        input: testCases[i]?.input || '',
        expected: r.expected,
        actual: r.actual,
        message: r.message,
      }))

      setTestResults(results)

      const allPassed = batchResult.passed_count === batchResult.total_count
      setFeedbackState(allPassed ? 'correct' : 'wrong')

      // Submit to backend
      if (session) {
        await submitInfiniteExercise(courseId, session.session_id, {
          exercise_id: currentExercise.id,
          code: code,
          language: language,
          test_results: results
        }, token)

        // Update progress
        setExerciseProgress(prev => {
          const newProgress = [...prev]
          const idx = newProgress.findIndex(p => p.exercise_id === currentExercise.id)
          if (idx >= 0) {
            newProgress[idx] = {
              ...newProgress[idx],
              is_completed: true,
              is_correct: allPassed,
              is_unlocked: true
            }
          }
          // Unlock next exercise
          if (allPassed && idx < newProgress.length - 1) {
            newProgress[idx + 1] = { ...newProgress[idx + 1], is_unlocked: true }
          } else if (!allPassed && idx < newProgress.length - 1) {
            // Also unlock next on wrong answer
            newProgress[idx + 1] = { ...newProgress[idx + 1], is_unlocked: true }
          }
          return newProgress
        })
      }

      // Save code for this language
      setSavedCodes(prev => ({
        ...prev,
        [currentExercise.id]: {
          ...prev[currentExercise.id],
          [language]: code
        }
      }))

      if (allPassed) {
        setXpEarned(prev => prev + 10)
      }

      // Show modal for correct answers
      if (allPassed) {
        setModalResult({
          isCorrect: true,
          passedCount: batchResult.passed_count,
          totalCount: batchResult.total_count,
          xpEarned: 10
        })
        setShowResultModal(true)
      }

    } catch (error) {
      console.error('Failed to submit:', error)
      setFeedbackState('wrong')
      setTestResults([{
        passed: false,
        input: '',
        expected: '',
        actual: '',
        message: '提交失败，请重试'
      }])
    } finally {
      setIsSubmitting(false)
    }
  }

  // ========================================
  // Navigation
  // ========================================

  const switchToExercise = useCallback(async (index: number) => {
    if (index < 0 || index >= exercises.length) return

    const currentExercise = exercises[currentIndex]
    const targetExercise = exercises[index]

    // Check if unlocked
    const targetProgress = exerciseProgress.find(p => p.exercise_id === targetExercise.id)
    if (targetProgress && !targetProgress.is_unlocked) {
      return // Can't switch to locked exercise
    }

    // Save current code
    if (currentExercise) {
      setSavedCodes(prev => ({
        ...prev,
        [currentExercise.id]: {
          ...prev[currentExercise.id],
          [language]: codeRef.current
        }
      }))
    }

    setCurrentIndex(index)

    // Restore code for target exercise
    const savedCodeForLang = savedCodes[targetExercise.id]?.[language]
    if (savedCodeForLang) {
      setCode(savedCodeForLang)
    } else {
      setCode(targetExercise.content.code_template || getTemplate(language))
    }

    setTestResults([])
    setFeedbackState('idle')
    setRightPanelTab('code')
    setCustomTestOutput(null)
    setShowResultModal(false)
  }, [exercises, currentIndex, exerciseProgress, savedCodes, language])

  const handleNext = useCallback(() => {
    setShowResultModal(false)
    if (currentIndex < exercises.length - 1) {
      switchToExercise(currentIndex + 1)
    }
  }, [currentIndex, exercises.length, switchToExercise])

  const handleStay = useCallback(() => {
    setShowResultModal(false)
  }, [])

  const handleRetry = useCallback(() => {
    setTestResults([])
    setFeedbackState('idle')
    setCustomTestOutput(null)
    setRightPanelTab('code')
    setShowResultModal(false)
  }, [])

  // ========================================
  // Exit
  // ========================================

  const handleExitSave = useCallback(async () => {
    const token = localStorage.getItem('token')
    const currentExercise = exercises[currentIndex]

    if (token && session && currentExercise) {
      try {
        await exitInfiniteSession(courseId, session.session_id, {
          current_exercise_id: currentExercise.id,
          current_code: codeRef.current,
          current_language: language
        }, token)
      } catch (error) {
        console.error('Failed to save on exit:', error)
      }
    }
  }, [courseId, session, exercises, currentIndex, language])

  const handleExit = async () => {
    await handleExitSave()
    router.push('/dashboard')
  }

  // ========================================
  // Difficulty names
  // ========================================

  const DIFFICULTY_NAMES: Record<number, string> = {
    1: '入门',
    2: '普及-',
    3: '普及/提高-',
    4: '普及+/提高',
    5: '提高+/省选-',
    6: '省选/NOI-',
    7: 'NOI',
    8: 'NOI+/CTSC',
  }

  // ========================================
  // Loading State
  // ========================================

  if (loading && !session) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white to-[#F7F8FA] flex flex-col">
        <header className="h-[50px] bg-white border-b border-[#E4E7ED] flex items-center justify-between px-4">
          <div className="skeleton h-8 w-32 rounded-lg"></div>
          <div className="flex items-center gap-4">
            <div className="skeleton h-6 w-40 rounded-lg"></div>
            <div className="skeleton h-8 w-20 rounded-full"></div>
          </div>
        </header>
        <main className="flex-1 flex pt-[50px]">
          <div className="w-[40%] border-r border-[#E4E7ED] p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="skeleton h-8 w-20 rounded-lg"></div>
              <div className="skeleton h-6 w-16 rounded-lg"></div>
            </div>
            <div className="skeleton h-7 w-3/4 rounded mb-4"></div>
            <div className="space-y-3">
              <div className="skeleton h-4 w-full rounded"></div>
              <div className="skeleton h-4 w-full rounded"></div>
              <div className="skeleton h-4 w-2/3 rounded"></div>
            </div>
          </div>
          <div className="w-[60%] flex flex-col">
            <div className="h-12 bg-[#F5F7FA] border-b border-[#E4E7ED] flex items-center gap-2 px-4">
              <div className="skeleton h-8 w-16 rounded"></div>
              <div className="skeleton h-8 w-16 rounded"></div>
            </div>
            <div className="flex-1 bg-white">
              <div className="skeleton h-full w-full"></div>
            </div>
          </div>
        </main>
        <div className="h-[72px] bg-white border-t border-[#E4E7ED] flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <div className="skeleton h-8 w-8 rounded-lg"></div>
            <div className="skeleton h-4 w-32 rounded"></div>
          </div>
          <div className="flex gap-2">
            <div className="skeleton h-10 w-20 rounded-lg"></div>
            <div className="skeleton h-10 w-24 rounded-lg"></div>
          </div>
        </div>
      </div>
    )
  }

  // ========================================
  // Main IDE View
  // ========================================

  if (!session || exercises.length === 0) return null

  const currentExercise = exercises[currentIndex]
  const currentProgress = exerciseProgress.find(p => p.exercise_id === currentExercise.id)
  const isLastExercise = currentIndex === exercises.length - 1
  const passedCount = testResults.filter(r => r.passed).length
  const canGoNext = currentIndex < exercises.length - 1 &&
    exerciseProgress[currentIndex + 1]?.is_unlocked

  return (
    <div className="min-h-screen ide-container flex flex-col">
      {/* Top Bar */}
      <header className="fixed top-0 left-0 right-0 z-50 h-[50px] ide-header">
        <div className="h-full px-4 flex items-center justify-between">
          <button onClick={handleExit} className="ide-header-back">
            <X className="w-4 h-4" />
            <span className="text-sm">退出挑战</span>
          </button>

          <div className="flex items-center gap-4">
            {/* Exercise Navigation */}
            <ExerciseNavigation
              exercises={exerciseProgress}
              currentIndex={currentIndex}
              onSwitch={switchToExercise}
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#3498DB]/10 rounded-full">
              <Zap className="w-4 h-4 text-[#F39C11]" />
              <span className="font-bold text-sm text-[#F39C11]">{xpEarned} XP</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex pt-[50px] h-[calc(100vh-50px)] overflow-hidden">
        {/* Left: Problem Panel */}
        <div className="w-[40%] ide-problem-panel bg-white flex-shrink-0" style={{ maxHeight: 'calc(100vh - 50px)', overflowY: 'auto', overflowX: 'hidden' }}>
          {currentExercise && (
            <div className="p-6">
              <div className="flex items-center gap-3 mb-6">
                <span className={`px-3 py-1 rounded-lg text-xs font-bold text-white difficulty-badge difficulty-${currentExercise.difficulty}`}>
                  {DIFFICULTY_NAMES[currentExercise.difficulty] || `难度 ${currentExercise.difficulty}`}
                </span>
                <span className="text-sm text-[#909399]">第 {currentIndex + 1} 题</span>
              </div>

              {currentExercise.content.description && (
                <div className="prose prose-sm max-w-none mb-6">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      h2: ({ children }) => (
                        <h3 className="text-base font-semibold text-[#303133] mt-4 mb-2 border-b border-[#E4E7ED] pb-2">{children}</h3>
                      ),
                      p: ({ children }) => (
                        <p className="text-[#606266] mb-2 leading-relaxed">{children}</p>
                      ),
                      code: ({ className, children, ...props }) => {
                        const isInline = !className
                        return isInline ? (
                          <code className="bg-[#F5F7FA] px-1.5 py-0.5 rounded text-sm text-[#E74C3C] font-mono border border-[#E4E7ED]" {...props}>{children}</code>
                        ) : (
                          <code className={className} {...props}>{children}</code>
                        )
                      },
                    }}
                  >
                    {currentExercise.content.description}
                  </ReactMarkdown>
                </div>
              )}

              {/* Sample I/O */}
              {currentExercise.content.samples && currentExercise.content.samples.length > 0 ? (
                <div className="mb-6">
                  <SampleIOCard
                    input={currentExercise.content.samples[0].input}
                    output={currentExercise.content.samples[0].output}
                    onRun={(input) => handleSampleRun(input, currentExercise.content.samples![0].output)}
                    isRunning={isCustomRunning}
                  />
                </div>
              ) : (currentExercise.content.sample_input || currentExercise.content.sample_output) ? (
                <div className="mb-6">
                  <SampleIOCard
                    input={currentExercise.content.sample_input || ''}
                    output={currentExercise.content.sample_output || ''}
                    onRun={(input) => handleSampleRun(input, currentExercise.content.sample_output)}
                    isRunning={isCustomRunning}
                  />
                </div>
              ) : null}

              {currentExercise.knowledge_points.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {currentExercise.knowledge_points.map((kp, i) => (
                    <span key={i} className="knowledge-tag px-3 py-1.5 text-[#3498DB] text-xs rounded-lg font-medium">
                      {kp}
                    </span>
                  ))}
                </div>
              )}

              {/* Profile info */}
              {profile && (
                <div className="mt-6 bg-[#3498DB]/5 rounded-xl border border-[#3498DB]/20 p-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{TIER_ICONS[profile.tier]}</span>
                    <div>
                      <p className="font-medium text-[#303133]">{TIER_NAMES[profile.tier]}</p>
                      <p className="text-sm text-[#606266]">
                        总积分: <span className="text-[#3498DB] font-medium">{profile.total_score.toFixed(0)}</span>
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Code Editor + Test Panel */}
        <div className="w-[60%] flex flex-col ide-editor-panel bg-white flex-shrink-0" style={{ maxHeight: 'calc(100vh - 50px)', overflow: 'hidden' }}>
          {/* Tab Header */}
          <div className="panel-tabs flex-shrink-0 flex items-center justify-between">
            <div className="flex">
              <button
                onClick={() => setRightPanelTab('code')}
                className={`panel-tab ${rightPanelTab === 'code' ? 'active' : ''}`}
              >
                <Code2 className="w-4 h-4 inline mr-1.5" />
                代码
              </button>
              <button
                onClick={() => setRightPanelTab('test')}
                className={`panel-tab ${rightPanelTab === 'test' ? 'active' : ''}`}
              >
                <Terminal className="w-4 h-4 inline mr-1.5" />
                测试
              </button>
              {testResults.length > 0 && (
                <button
                  onClick={() => setRightPanelTab('output')}
                  className={`panel-tab ${rightPanelTab === 'output' ? 'active' : ''}`}
                >
                  <CheckCircle className="w-4 h-4 inline mr-1.5" />
                  结果
                </button>
              )}
            </div>
            <div className="flex items-center gap-2 pr-3">
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="px-2 py-1 text-xs font-medium text-[#606266] bg-white border border-[#E4E7ED] rounded-md focus:outline-none focus:border-[#3498DB] cursor-pointer"
              >
                {LANGUAGE_OPTIONS.map((lang) => (
                  <option key={lang.key} value={lang.key}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden">
            {rightPanelTab === 'code' && (
              <CodeEditorPanel
                value={code}
                onChange={setCode}
                language={LANGUAGE_MAP[language]?.monaco || 'python'}
              />
            )}

            {rightPanelTab === 'test' && (
              <div className="h-full overflow-y-auto p-4 bg-[#FAFBFC]">
                <CustomTestInput
                  onRun={(input) => handleCustomRun(input, false)}
                  isRunning={isCustomRunning}
                  defaultInput={customTestInput}
                />
                {customTestOutput && (
                  <div className="mt-4">
                    <TestOutputDisplay
                      output={customTestOutput.output}
                      expected={customTestOutput.expected}
                      passed={customTestOutput.passed}
                      isRunning={isCustomRunning}
                      error={customTestOutput.error}
                    />
                  </div>
                )}
              </div>
            )}

            {rightPanelTab === 'output' && (
              <div className="h-full overflow-y-auto p-4 bg-[#FAFBFC]">
                <LuoguTestCaseTable
                  results={testResults}
                  passedCount={passedCount}
                  totalCount={testResults.length}
                  isRunning={isSubmitting}
                />
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Bottom Action Bar */}
      <div className={`ide-action-bar ${
        feedbackState === 'correct' ? 'ide-action-bar-success' :
        feedbackState === 'wrong' ? 'ide-action-bar-error' :
        'ide-action-bar-idle'
      }`}>
        <div className="px-6 py-4">
          {feedbackState === 'idle' ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-[#3498DB]/10 rounded-lg flex items-center justify-center border border-[#3498DB]/20">
                    <Zap className="w-5 h-5 text-[#F39C11]" />
                  </div>
                  <div>
                    <p className="text-sm text-[#303133] font-medium">无限模式</p>
                    <p className="text-xs text-[#909399]">
                      已获得 <span className="text-[#F39C11] font-medium">{xpEarned}</span> XP
                    </p>
                  </div>
                </div>

                {testResults.length > 0 && (
                  <>
                    <div className="h-6 w-px bg-[#E4E7ED]" />
                    <LuoguTestCasesSummary
                      passedCount={passedCount}
                      totalCount={testResults.length}
                    />
                  </>
                )}
              </div>

              <div className="action-buttons-group">
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="btn-action btn-submit"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      提交中...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      提交
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : feedbackState === 'correct' ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#52C41A]/10 rounded-lg flex items-center justify-center border border-[#52C41A]/20 success-pulse">
                  <CheckCircle className="w-6 h-6 text-[#52C41A]" />
                </div>
                <div>
                  <p className="font-semibold text-[#52C41A]">太棒了！全部通过</p>
                  <p className="text-sm text-[#52C41A]/70">
                    +10 XP
                  </p>
                </div>
              </div>
              <div className="action-buttons-group">
                <button
                  onClick={handleRetry}
                  className="btn-action btn-reset"
                >
                  <RotateCcw className="w-4 h-4" />
                  重新作答
                </button>
                {canGoNext && (
                  <button
                    onClick={handleNext}
                    className="btn-action btn-success"
                  >
                    下一题
                    <ArrowRight className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#E74C3C]/10 rounded-lg flex items-center justify-center border border-[#E74C3C]/20 error-shake">
                  <XCircle className="w-6 h-6 text-[#E74C3C]" />
                </div>
                <div>
                  <p className="font-semibold text-[#E74C3C]">答案错误</p>
                  {testResults.length > 0 && (
                    <p className="text-sm text-[#E74C3C]/70">
                      通过 {passedCount}/{testResults.length} 个测试点 · 修改后重新提交
                    </p>
                  )}
                </div>
              </div>
              <div className="action-buttons-group">
                <button
                  onClick={handleRetry}
                  className="btn-action btn-reset"
                >
                  <RotateCcw className="w-4 h-4" />
                  重新作答
                </button>
                {testResults.length > 0 && (
                  <button
                    onClick={() => setRightPanelTab('output')}
                    className="btn-action btn-submit"
                  >
                    查看详情
                  </button>
                )}
                {canGoNext && (
                  <button
                    onClick={handleNext}
                    className="btn-action btn-success"
                  >
                    下一题
                    <ArrowRight className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Result Modal */}
      {showResultModal && modalResult && (
        <ResultModal
          isCorrect={modalResult.isCorrect}
          passedCount={modalResult.passedCount}
          totalCount={modalResult.totalCount}
          xpEarned={modalResult.xpEarned}
          onStay={handleStay}
          onNext={handleNext}
          canGoNext={canGoNext}
        />
      )}
    </div>
  )
}
