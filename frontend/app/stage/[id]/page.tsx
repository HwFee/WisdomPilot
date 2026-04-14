'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState, useCallback, useRef } from 'react'
import {
  X, Zap, CheckCircle, XCircle, ArrowRight, RotateCcw, Play,
  Sparkles, Target, ChevronRight, RefreshCw, Loader2, BookOpen,
  Code2, Terminal, Send, Save, ArrowLeft, ChevronLeft, ChevronRight as ChevronRightIcon
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import { getStage, startStage, getStageExercises, completePractice, startVerification, submitVerification, getKnowledgeCheck } from '@/lib/api/stages'
import { submitExercise } from '@/lib/api/exercises'
import { executeCode, executeCodeBatch } from '@/lib/api/code'
import { CodeEditorPanel } from '@/components/exercise/CodeEditorPanel'
import { KnowledgeCheckModal } from '@/components/stage/KnowledgeCheckModal'
import { SampleIOCard } from '@/components/exercise/SampleIOCard'
import { TestCasesPanel, TestCasesSummary } from '@/components/exercise/TestCasesPanel'
import { CustomTestInput, TestOutputDisplay } from '@/components/exercise/CustomTestInput'
import { LuoguTestCaseTable, LuoguTestCasesSummary } from '@/components/exercise/LuoguTestCaseTable'
import { getExerciseRecommendations, type ExerciseRecommendItem, type KnowledgeState } from '@/lib/api/vector'
import { triggerDashboardRefresh } from '@/lib/events/dashboard'
import { startStageSession, endLearningSession, getActiveSession } from '@/lib/api/stats'

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
  }
  knowledge_points: string[]
  hints?: string[]
  test_cases?: Array<{input: string, output: string, name?: string}>
  solution?: {
    answer?: string
    explanation?: string
  }
}

interface Stage {
  id: number
  title: string
  description: string
  difficulty_level: number
  required_exercises: number
  required_accuracy: number
  xp_reward: number
  quota_bonus: number
  learning_objectives?: string[]
}

interface Progress {
  id: string
  status: string
  exercises_completed: number
  exercises_correct: number
  accuracy: number
  verification_started: boolean
  verification_passed: boolean
  current_exercise_index?: number
  saved_code?: string
}

// 追踪每道题的完成状态
interface ExerciseState {
  completed: boolean
  correct: boolean
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

type FeedbackState = 'idle' | 'correct' | 'wrong'
type RightPanelTab = 'code' | 'test' | 'output'

// ========================================
// Language Configuration
// ========================================

interface LanguageConfig {
  id: number        // Judge0 language_id
  name: string      // 显示名称
  monaco: string    // Monaco Editor language
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

// 课程类型到默认语言的映射
const COURSE_DEFAULT_LANGUAGE: Record<string, string> = {
  'c': 'c',
  'cpp': 'cpp',
  'c++': 'cpp',
  'python': 'python',
  'java': 'java',
  'rust': 'rust',
}

// ========================================
// Storage Keys
// ========================================

const getStorageKey = (stageId: number) => ({
  code: `stage_${stageId}_code`,
  exerciseIndex: `stage_${stageId}_exercise_index`,
  progress: `stage_${stageId}_progress`,
  exerciseStates: `stage_${stageId}_exercise_states`,
  exerciseCodes: `stage_${stageId}_exercise_codes`,
  exerciseResults: `stage_${stageId}_exercise_results`,
})

// ========================================
// Main Component
// ========================================

export default function StagePage() {
  const params = useParams()
  const router = useRouter()
  const stageId = parseInt(params.id as string)

  // State
  const [stage, setStage] = useState<Stage | null>(null)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answer, setAnswer] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const [feedbackState, setFeedbackState] = useState<FeedbackState>('idle')
  const [loading, setLoading] = useState(true)
  const [code, setCode] = useState('')
  const [showVerification, setShowVerification] = useState(false)
  const [verificationQuestions, setVerificationQuestions] = useState<any[]>([])
  const [verificationAnswers, setVerificationAnswers] = useState<Record<string, string>>({})
  const [verificationResult, setVerificationResult] = useState<any>(null)
  const [xpEarned, setXpEarned] = useState(0)

  // Language state
  const [language, setLanguage] = useState<string>('cpp')  // 默认 C++

  // New state for test cases and custom test
  const [rightPanelTab, setRightPanelTab] = useState<RightPanelTab>('code')
  const [testResults, setTestResults] = useState<TestCaseResult[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [customTestInput, setCustomTestInput] = useState('')
  const [customTestOutput, setCustomTestOutput] = useState<{
    output?: string
    expected?: string
    passed?: boolean
    error?: string
  } | null>(null)
  const [isCustomRunning, setIsCustomRunning] = useState(false)
  const [autoSaveStatus, setAutoSaveStatus] = useState<'saved' | 'saving' | 'idle'>('idle')

  // Recommendations state
  const [recommendations, setRecommendations] = useState<ExerciseRecommendItem[]>([])
  const [knowledgeState, setKnowledgeState] = useState<KnowledgeState | null>(null)
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)

  // Knowledge check state
  const [showKnowledgeCheck, setShowKnowledgeCheck] = useState(false)
  const [knowledgeCheckQuestions, setKnowledgeCheckQuestions] = useState<any[]>([])
  const [pendingNavigation, setPendingNavigation] = useState<'next' | 'verify' | null>(null)

  // 追踪每道题的完成状态（本地）
  const [exerciseStates, setExerciseStates] = useState<ExerciseState[]>([])

  // 每道题保存的代码
  const [exerciseCodes, setExerciseCodes] = useState<Record<number, string>>({})

  // 每道题保存的测试结果
  const [exerciseResults, setExerciseResults] = useState<Record<number, { results: TestCaseResult[], feedbackState: FeedbackState }>>({})

  // Refs
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const codeRef = useRef(code)
  codeRef.current = code

  // 学习会话追踪
  const sessionStartRef = useRef<Date | null>(null)
  const sessionIdRef = useRef<string | null>(null)

  // ========================================
  // Data Fetching
  // ========================================

  const fetchRecommendations = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      setRecommendationsLoading(true)
      const data = await getExerciseRecommendations(token, { limit: 5 })
      setRecommendations(data.recommendations)
      setKnowledgeState(data.knowledge_state)
    } catch (error) {
      console.error('Failed to fetch recommendations:', error)
    } finally {
      setRecommendationsLoading(false)
    }
  }, [])

  const fetchStageData = useCallback(async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) return

      const stageData = await getStage(stageId, token)
      setStage(stageData.stage as Stage)
      setProgress(stageData.progress as Progress | null)

      // 设置默认语言：优先用户上次选择 > 课程关联语言 > 默认 C++
      const savedLanguage = localStorage.getItem('preferred_language')
      if (savedLanguage && LANGUAGE_MAP[savedLanguage]) {
        setLanguage(savedLanguage)
      } else if (stageData.stage) {
        // 尝试从课程名称推断语言
        const courseName = (stageData.stage as any).course_name || ''
        const courseLower = courseName.toLowerCase()
        for (const [key, _] of Object.entries(COURSE_DEFAULT_LANGUAGE)) {
          if (courseLower.includes(key)) {
            setLanguage(COURSE_DEFAULT_LANGUAGE[key])
            break
          }
        }
      }

      try {
        const exercisesData = await getStageExercises(stageId, token)
        // 处理样例：如果为空，从测试点第一组数据提取
        const exerciseList = (exercisesData.exercises as Exercise[]).map(ex => {
          // 如果已有样例，直接返回
          if (ex.content.sample_input || ex.content.sample_output) {
            return ex
          }
          // 如果有测试点，用第一组作为样例
          if (ex.test_cases && ex.test_cases.length > 0) {
            return {
              ...ex,
              content: {
                ...ex.content,
                sample_input: ex.test_cases[0].input || '',
                sample_output: ex.test_cases[0].output || '',
              }
            }
          }
          return ex
        })
        setExercises(exerciseList)

        const keys = getStorageKey(stageId)

        // 加载每道题的状态
        const savedStates = localStorage.getItem(keys.exerciseStates)
        let loadedStates: ExerciseState[] = exerciseList.map(() => ({ completed: false, correct: false }))

        if (savedStates) {
          try {
            const parsed = JSON.parse(savedStates)
            if (Array.isArray(parsed) && parsed.length === exerciseList.length) {
              loadedStates = parsed
            }
          } catch (e) {
            console.error('Failed to parse exercise states:', e)
          }
        }
        setExerciseStates(loadedStates)

        // 加载每道题保存的代码
        const savedCodes = localStorage.getItem(keys.exerciseCodes)
        let loadedCodes: Record<number, string> = {}
        if (savedCodes) {
          try {
            loadedCodes = JSON.parse(savedCodes)
          } catch (e) {
            console.error('Failed to parse exercise codes:', e)
          }
        }
        setExerciseCodes(loadedCodes)

        // 加载每道题保存的测试结果
        const savedResults = localStorage.getItem(keys.exerciseResults)
        let loadedResults: Record<number, { results: TestCaseResult[], feedbackState: FeedbackState }> = {}
        if (savedResults) {
          try {
            loadedResults = JSON.parse(savedResults)
          } catch (e) {
            console.error('Failed to parse exercise results:', e)
          }
        }
        setExerciseResults(loadedResults)

        // Load saved progress
        const savedIndex = localStorage.getItem(keys.exerciseIndex)
        let startIdx = 0

        if (stageData.progress && typeof (stageData.progress as any).current_exercise_index === 'number') {
          startIdx = (stageData.progress as any).current_exercise_index
        } else if (savedIndex !== null) {
          startIdx = parseInt(savedIndex)
        }

        if (startIdx >= 0 && startIdx < exerciseList.length) {
          setCurrentIndex(startIdx)
          // 优先使用保存的代码，否则使用模板
          const savedCodeForExercise = loadedCodes[startIdx]
          const templateCode = exerciseList[startIdx].content.code_template || ''
          setCode(savedCodeForExercise || templateCode)

          // 恢复这道题的测试结果状态
          const savedResultForExercise = loadedResults[startIdx]
          if (savedResultForExercise) {
            setTestResults(savedResultForExercise.results)
            setFeedbackState(savedResultForExercise.feedbackState)
            setSubmitted(savedResultForExercise.feedbackState !== 'idle')
          } else {
            setTestResults([])
            setFeedbackState('idle')
            setSubmitted(false)
          }
        } else if (exerciseList.length > 0) {
          setCode(exerciseList[0].content.code_template || '')
        }
      } catch {
        setExercises([])
      }

      fetchRecommendations()
    } catch (error) {
      console.error('Failed to fetch stage data:', error)
    } finally {
      setLoading(false)
    }
  }, [stageId, fetchRecommendations])

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }
    fetchStageData()
  }, [fetchStageData, router])

  // ========================================
  // Learning Session Management
  // ========================================

  // 开始学习会话
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token || !stageId) return

    // 记录会话开始时间
    sessionStartRef.current = new Date()

    // 开始学习会话
    const startSession = async () => {
      try {
        const session = await startStageSession(token, stageId)
        sessionIdRef.current = session.id
        console.log('Learning session started:', session.id)
      } catch (error) {
        console.error('Failed to start learning session:', error)
      }
    }

    startSession()

    // 页面离开时结束会话
    const endSession = async () => {
      if (!sessionStartRef.current) return

      const duration = Math.floor((new Date().getTime() - sessionStartRef.current.getTime()) / 1000)
      if (duration < 10) return // 少于10秒不记录

      try {
        const token = localStorage.getItem('token')
        if (token) {
          await endLearningSession(token, duration)
          console.log('Learning session ended, duration:', duration, 'seconds')
        }
      } catch (error) {
        console.error('Failed to end learning session:', error)
      }
    }

    // 监听页面离开事件
    const handleBeforeUnload = () => {
      endSession()
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        endSession()
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      endSession()
    }
  }, [stageId])

  // ========================================
  // Auto Save
  // ========================================

  // 保存当前题目的代码 - 使用 useRef 避免依赖循环
  const exerciseCodesRef = useRef(exerciseCodes)
  exerciseCodesRef.current = exerciseCodes

  const saveExerciseCode = useCallback((index: number, codeValue: string) => {
    const keys = getStorageKey(stageId)
    const newCodes = { ...exerciseCodesRef.current, [index]: codeValue }
    exerciseCodesRef.current = newCodes
    setExerciseCodes(newCodes)
    localStorage.setItem(keys.exerciseCodes, JSON.stringify(newCodes))
  }, [stageId])

  // 保存当前题目的测试结果 - 使用 useRef 避免依赖循环
  const exerciseResultsRef = useRef(exerciseResults)
  exerciseResultsRef.current = exerciseResults

  const saveExerciseResult = useCallback((index: number, results: TestCaseResult[], state: FeedbackState) => {
    const keys = getStorageKey(stageId)
    const newResults = { ...exerciseResultsRef.current, [index]: { results, feedbackState: state } }
    exerciseResultsRef.current = newResults
    setExerciseResults(newResults)
    localStorage.setItem(keys.exerciseResults, JSON.stringify(newResults))
  }, [stageId])

  const saveProgress = useCallback(async (currentIdx: number, currentCode: string) => {
    setAutoSaveStatus('saving')
    const keys = getStorageKey(stageId)
    localStorage.setItem(keys.code, currentCode)
    localStorage.setItem(keys.exerciseIndex, currentIdx.toString())

    // 同时保存到 exerciseCodes
    saveExerciseCode(currentIdx, currentCode)

    // Try to save to backend as well
    try {
      const token = localStorage.getItem('token')
      if (token && progress?.id) {
        // Could add a saveProgress API call here if backend supports it
      }
    } catch (error) {
      console.error('Failed to save progress to backend:', error)
    }

    setAutoSaveStatus('saved')
    setTimeout(() => setAutoSaveStatus('idle'), 2000)
  }, [stageId, progress])

  // 保存题目状态到 localStorage
  const saveExerciseStates = useCallback((states: ExerciseState[]) => {
    const keys = getStorageKey(stageId)
    localStorage.setItem(keys.exerciseStates, JSON.stringify(states))
  }, [stageId])

  // Auto save on code change with debounce - 不依赖 saveProgress 避免循环
  useEffect(() => {
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current)
    }

    autoSaveTimeoutRef.current = setTimeout(() => {
      if (code && currentIndex !== undefined) {
        // 直接保存，不调用 saveProgress
        const keys = getStorageKey(stageId)
        localStorage.setItem(keys.code, code)
        localStorage.setItem(keys.exerciseIndex, currentIndex.toString())
        saveExerciseCode(currentIndex, code)
      }
    }, 2000)

    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current)
      }
    }
  }, [code, currentIndex, stageId, saveExerciseCode])

  // ========================================
  // Event Handlers
  // ========================================

  const handleStartStage = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const data = await startStage(stageId, token)
      setProgress(data.progress as Progress)
    } catch (error) {
      console.error('Failed to start stage:', error)
    }
  }

  // 难度名称映射（洛谷体系）
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

  // 语言切换处理
  const handleLanguageChange = (newLang: string) => {
    if (newLang === language) return
    setLanguage(newLang)
    setCode('')  // 清空编辑器
    localStorage.setItem('preferred_language', newLang)
  }

  // 获取当前语言的 Judge0 ID
  const getLanguageId = () => LANGUAGE_MAP[language]?.id || 54  // 默认 C++

  // Run with custom input - isFromSample 表示是否从样例运行触发
  const handleCustomRun = async (input: string, isFromSample: boolean = false) => {
    if (!code || isCustomRunning) return

    setIsCustomRunning(true)
    setCustomTestOutput(null)
    // 样例运行时跳转到测试标签页，手动测试保持当前标签页
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
      setCustomTestOutput({
        error: '运行失败，请重试',
      })
    } finally {
      setIsCustomRunning(false)
    }
  }

  // Run with sample input - 跳转到测试标签页
  const handleSampleRun = async (input: string) => {
    setCustomTestInput(input)
    await handleCustomRun(input, true)  // isFromSample = true
  }

  // Submit answer (runs all test cases)
  const handleSubmit = async () => {
    if (!exercises[currentIndex]) return

    const currentExercise = exercises[currentIndex]
    const isProgramming = currentExercise.type === 'programming'

    if (!isProgramming && !answer) return

    setSubmitted(true)

    try {
      const token = localStorage.getItem('token')
      if (!token) return

      // Choice questions
      if (!isProgramming) {
        const result = await submitExercise(
          currentExercise.id,
          { answer: answer },
          token
        )

        const correct = result.is_correct
        setFeedbackState(correct ? 'correct' : 'wrong')

        // 更新本地题目状态（允许重新提交更新状态）
        setExerciseStates(prev => {
          const newStates = [...prev]
          newStates[currentIndex] = { completed: true, correct }
          saveExerciseStates(newStates)
          return newStates
        })

        const completedCount = exerciseStates.filter((s, i) =>
          i === currentIndex ? true : s?.completed
        ).length
        const correctCount = exerciseStates.filter((s, i) =>
          i === currentIndex ? correct : s?.correct
        ).length

        // 只发送当前完成的题目（不要发送所有已完成的题目）
        const completedExercises = [{
          exercise_id: exercises[currentIndex].id,
          exercise_title: exercises[currentIndex].content.title || exercises[currentIndex].content.text,
          is_correct: correct,
        }]

        await completePractice(stageId, {
          exercises_completed: completedCount,
          exercises_correct: correctCount,
          completed_exercises: completedExercises,
        }, token)

        // 触发仪表盘刷新
        triggerDashboardRefresh({
          exerciseId: currentExercise.id,
          exerciseTitle: currentExercise.content.title || currentExercise.content.text,
          stageId: stageId,
          stageName: stage?.title,
          correct: correct,
        })

        if (correct) {
          setXpEarned(prev => prev + Math.round((stage?.xp_reward || 0) / (exercises.length || 1)))
        }
      } else {
        // Programming questions - submit to run all test cases
        setIsSubmitting(true)
        setTestResults([])
        setRightPanelTab('output')

        try {
          const testCases = currentExercise.test_cases || []

          if (testCases.length === 0) {
            setTestResults([{
              passed: false,
              input: '',
              expected: '',
              actual: '',
              message: '该题目暂无测试用例，无法验证'
            }])
            setFeedbackState('wrong')
            return
          }

          // Batch execute all test cases
          const batchResult = await executeCodeBatch({
            code: code,
            language_id: getLanguageId(),
            test_cases: testCases.map(tc => ({
              input: tc.input || '',
              expected_output: tc.output || ''
            }))
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
          const newFeedbackState = allPassed ? 'correct' : 'wrong'
          setFeedbackState(newFeedbackState)

          // 保存测试结果
          saveExerciseResult(currentIndex, results, newFeedbackState)

          // 保存代码
          saveExerciseCode(currentIndex, code)

          // 更新本地题目状态（允许重新提交更新状态）
          setExerciseStates(prev => {
            const newStates = [...prev]
            newStates[currentIndex] = { completed: true, correct: allPassed }
            saveExerciseStates(newStates)
            return newStates
          })

          // 计算实际进度
          const updatedStates = exerciseStates.map((s, i) =>
            i === currentIndex ? { completed: true, correct: allPassed } : s
          )
          const completedCount = updatedStates.filter(s => s?.completed).length
          const correctCount = updatedStates.filter(s => s?.correct).length

          // 构建完成的练习题列表
          // 只发送当前完成的题目（不要发送所有已完成的题目）
          const completedExercises = [{
            exercise_id: exercises[currentIndex].id,
            exercise_title: exercises[currentIndex].content.title || exercises[currentIndex].content.text,
            is_correct: allPassed,
          }]

          await completePractice(stageId, {
            exercises_completed: completedCount,
            exercises_correct: correctCount,
            completed_exercises: completedExercises,
          }, token)

          // 触发仪表盘刷新
          triggerDashboardRefresh({
            exerciseId: currentExercise.id,
            exerciseTitle: currentExercise.content.title || currentExercise.content.text,
            stageId: stageId,
            stageName: stage?.title,
            correct: allPassed,
          })

          if (allPassed) {
            setXpEarned(prev => prev + Math.round((stage?.xp_reward || 0) / (exercises.length || 1)))

            // Save progress
            await saveProgress(currentIndex, code)

            // Get knowledge check questions
            try {
              const kcData = await getKnowledgeCheck(stageId, {
                exercise_id: currentExercise.id,
                count: 3
              }, token)
              setKnowledgeCheckQuestions(kcData.questions)
              setPendingNavigation(isLastExercise ? 'verify' : 'next')
            } catch (error) {
              console.error('Failed to get knowledge check:', error)
            }
          }
        } finally {
          setIsSubmitting(false)
        }
      }
    } catch (error) {
      console.error('Failed to submit answer:', error)
      setFeedbackState('wrong')
      setTestResults([{
        passed: false,
        input: '',
        expected: '',
        actual: '',
        message: '提交失败，请重试'
      }])
    }
  }

  // 切换题目 - 恢复保存的代码和结果
  const switchToExercise = useCallback((index: number) => {
    if (index < 0 || index >= exercises.length) return

    // 先保存当前题目的代码
    saveExerciseCode(currentIndex, code)

    setCurrentIndex(index)

    // 恢复这道题保存的代码
    const savedCode = exerciseCodesRef.current[index]
    const templateCode = exercises[index].content.code_template || ''
    setCode(savedCode || templateCode)

    // 恢复这道题保存的测试结果
    const savedResult = exerciseResultsRef.current[index]
    if (savedResult) {
      setTestResults(savedResult.results)
      setFeedbackState(savedResult.feedbackState)
      setSubmitted(savedResult.feedbackState !== 'idle')
      if (savedResult.feedbackState !== 'idle') {
        setRightPanelTab('output')
      } else {
        setRightPanelTab('code')
      }
    } else {
      setTestResults([])
      setFeedbackState('idle')
      setSubmitted(false)
      setRightPanelTab('code')
    }

    setAnswer(null)
    setCustomTestOutput(null)

    // 保存当前题目索引到 localStorage
    const keys = getStorageKey(stageId)
    localStorage.setItem(keys.exerciseIndex, index.toString())
  }, [currentIndex, code, exercises.length, exercises, saveExerciseCode, stageId])

  const handlePrev = useCallback(() => {
    if (currentIndex > 0) {
      switchToExercise(currentIndex - 1)
    }
  }, [currentIndex, switchToExercise])

  const handleNext = useCallback(() => {
    if (currentIndex < exercises.length - 1) {
      switchToExercise(currentIndex + 1)
    }
  }, [currentIndex, exercises.length, switchToExercise])

  // 切换到指定题目
  const handleGoToExercise = useCallback((index: number) => {
    switchToExercise(index)
  }, [switchToExercise])

  // 重试 - 重置当前题目状态
  const handleRetry = useCallback(() => {
    setSubmitted(false)
    setFeedbackState('idle')
    setTestResults([])
    setCustomTestOutput(null)
    setRightPanelTab('code')
    // 清除保存的结果
    saveExerciseResult(currentIndex, [], 'idle')
  }, [currentIndex, saveExerciseResult])

  // 留在该题 - 关闭成功/失败提示，回到正常状态
  const handleStayOnCurrent = useCallback(() => {
    setFeedbackState('idle')
    setSubmitted(false)
    // 保持当前代码和答案，让用户可以继续查看和修改
  }, [])

  const handleExit = () => {
    // Save before exit
    saveProgress(currentIndex, code)
    router.push(`/courses/${stage?.id}`)
  }

  const handleKnowledgeCheckComplete = (passed: boolean, correctCount: number) => {
    setShowKnowledgeCheck(false)
    setKnowledgeCheckQuestions([])

    if (passed && pendingNavigation) {
      if (pendingNavigation === 'next') {
        handleNext()
      } else if (pendingNavigation === 'verify') {
        handleStartVerification()
      }
    }
    setPendingNavigation(null)
  }

  const handleStartVerificationFlow = () => {
    if (knowledgeCheckQuestions.length > 0) {
      setShowKnowledgeCheck(true)
    } else {
      handleStartVerification()
    }
  }

  const handleStartVerification = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const data = await startVerification(stageId, token)
      setVerificationQuestions(data.questions)
      setShowVerification(true)
    } catch (error) {
      console.error('Failed to start verification:', error)
    }
  }

  const handleSubmitVerification = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const data = await submitVerification(stageId, { answers: verificationAnswers }, token)
      setVerificationResult(data)
    } catch (error) {
      console.error('Failed to submit verification:', error)
    }
  }

  // ========================================
  // Render Helpers
  // ========================================

  const currentExercise = exercises[currentIndex]
  const isLastExercise = currentIndex === exercises.length - 1
  const isProgramming = currentExercise?.type === 'programming'
  const passedCount = testResults.filter(r => r.passed).length

  // ========================================
  // Loading State - 浅色骨架屏
  // ========================================

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white to-[#F7F8FA] flex flex-col">
        {/* Header skeleton */}
        <header className="h-[50px] bg-white border-b border-[#E4E7ED] flex items-center justify-between px-4">
          <div className="skeleton h-8 w-32 rounded-lg"></div>
          <div className="flex items-center gap-4">
            <div className="skeleton h-6 w-40 rounded-lg"></div>
            <div className="skeleton h-8 w-20 rounded-full"></div>
          </div>
        </header>

        {/* Main content skeleton */}
        <main className="flex-1 flex pt-[50px]">
          {/* Left panel skeleton */}
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
            <div className="mt-6 skeleton h-32 w-full rounded-lg"></div>
          </div>

          {/* Right panel skeleton */}
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

        {/* Bottom bar skeleton */}
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

  if (!stage) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white to-[#F7F8FA] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-[#F5F7FA] rounded-2xl flex items-center justify-center mx-auto mb-4 border border-[#E4E7ED]">
            <X className="w-8 h-8 text-[#909399]" />
          </div>
          <h2 className="text-xl font-semibold text-[#303133] mb-2">关卡不存在</h2>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-[#3498DB] hover:underline"
          >
            返回仪表盘
          </button>
        </div>
      </div>
    )
  }

  // ========================================
  // Stage Not Started - 浅色主题
  // ========================================

  if (!progress || progress.status === 'locked') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white to-[#F7F8FA]">
        <header className="fixed top-0 left-0 right-0 z-50 h-[50px] bg-white border-b border-[#E4E7ED]">
          <div className="h-full flex items-center justify-between px-4">
            <button
              onClick={handleExit}
              className="ide-header-back"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">返回</span>
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#3498DB]/10 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-[#3498DB]" />
              </div>
              <span className="font-semibold text-[#303133]">关卡挑战</span>
            </div>
            <div className="w-20"></div>
          </div>
        </header>

        <section className="pt-28 pb-8 px-6">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <div className="w-24 h-24 bg-gradient-to-br from-[#3498DB] to-[#2980B9] rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-[#3498DB]/25">
                <Zap className="w-12 h-12 text-white" />
              </div>

              <h1 className="text-3xl font-bold text-[#303133] mb-3">{stage.title}</h1>
              <p className="text-[#606266] max-w-md mx-auto mb-8">{stage.description}</p>

              <div className="grid grid-cols-3 gap-4 max-w-md mx-auto mb-10">
                <div className="bg-white rounded-xl border border-[#E4E7ED] p-4 shadow-sm">
                  <p className="text-2xl font-bold text-[#303133]">{stage.required_exercises}</p>
                  <p className="text-xs text-[#909399]">练习题</p>
                </div>
                <div className="bg-white rounded-xl border border-[#E4E7ED] p-4 shadow-sm">
                  <p className="text-2xl font-bold text-[#303133]">{Math.round(stage.required_accuracy * 100)}%</p>
                  <p className="text-xs text-[#909399]">目标正确率</p>
                </div>
                <div className="bg-white rounded-xl border border-[#E4E7ED] p-4 shadow-sm">
                  <p className="text-2xl font-bold text-[#F39C11]">{stage.xp_reward}</p>
                  <p className="text-xs text-[#909399]">经验值</p>
                </div>
              </div>

              <button
                onClick={handleStartStage}
                className="px-10 py-4 bg-gradient-to-r from-[#3498DB] to-[#2980B9] text-white rounded-xl font-semibold text-lg hover:shadow-lg hover:shadow-[#3498DB]/25 transition-all inline-flex items-center gap-2"
              >
                <Play className="w-5 h-5" />
                开始挑战
              </button>
            </div>
          </div>
        </section>
      </div>
    )
  }

  // ========================================
  // Verification Modal
  // ========================================

  if (showVerification) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6">
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 max-w-3xl w-full">
          {verificationResult ? (
            <div className="py-6">
              {verificationResult.passed ? (
                <>
                  <div className="text-center mb-6">
                    <div className="w-24 h-24 bg-gradient-to-br from-emerald-400 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6">
                      <CheckCircle className="w-12 h-12 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">验证通过！</h2>
                    <p className="text-slate-400 mb-6">恭喜你完成了本关的所有挑战</p>
                    <div className="flex justify-center gap-4 mb-6">
                      <div className="bg-yellow-500/10 rounded-xl px-6 py-3 border border-yellow-500/20">
                        <span className="text-yellow-400 font-bold">+{verificationResult.xp_earned} XP</span>
                      </div>
                      <div className="bg-indigo-500/10 rounded-xl px-6 py-3 border border-indigo-500/20">
                        <span className="text-indigo-400 font-bold">+{verificationResult.quota_bonus} 配额</span>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="text-center mb-6">
                    <div className="w-24 h-24 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                      <XCircle className="w-12 h-12 text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">验证未通过</h2>
                    <p className="text-slate-400 mb-6">
                      答对 <span className="text-white font-bold">{verificationResult.correct_count}</span>/{verificationResult.total_count} 题
                    </p>
                    <p className="text-sm text-slate-500 mb-4">建议复习相关知识点后再试</p>
                  </div>
                </>
              )}
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="px-6 py-2.5 bg-slate-700 text-white rounded-xl font-medium hover:bg-slate-600 transition-colors"
                >
                  返回课程
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">关卡验证</h2>
                <span className="px-3 py-1 bg-slate-700 rounded-lg text-sm text-slate-300">
                  {verificationQuestions.length} 题
                </span>
              </div>

              <div className="space-y-5 mb-8 max-h-96 overflow-y-auto">
                {verificationQuestions.map((q, i) => (
                  <div key={q.id} className="bg-slate-700/30 rounded-xl p-5">
                    <p className="font-medium text-white mb-4">{i + 1}. {q.content.text}</p>
                    <div className="grid grid-cols-2 gap-2">
                      {q.content.options?.map((opt: string, j: number) => (
                        <button
                          key={j}
                          onClick={() => setVerificationAnswers({ ...verificationAnswers, [q.id]: opt })}
                          className={`p-3 rounded-xl border text-sm text-left transition-all ${
                            verificationAnswers[q.id] === opt
                              ? 'border-indigo-500 bg-indigo-500/20 text-white'
                              : 'border-slate-600 text-slate-300 hover:border-slate-500'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={handleSubmitVerification}
                disabled={Object.keys(verificationAnswers).length < verificationQuestions.length}
                className="w-full py-4 bg-gradient-to-r from-indigo-500 to-indigo-600 text-white rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                提交验证
              </button>
            </>
          )}
        </div>
      </div>
    )
  }

  // ========================================
  // Main IDE View
  // ========================================

  return (
    <div className="min-h-screen ide-container flex flex-col">
      {/* Top Bar */}
      <header className="fixed top-0 left-0 right-0 z-50 h-[50px] ide-header">
        <div className="h-full px-4 flex items-center justify-between">
          {/* Left: 返回按钮 */}
          <button
            onClick={handleExit}
            className="ide-header-back"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">返回题目列表</span>
          </button>

          {/* Center: Stage name + 题目导航 */}
          <div className="flex items-center gap-4">
            <span className="ide-header-title text-sm">{stage.title}</span>
            <div className="flex items-center gap-1.5">
              {exercises.map((_, i) => (
                <button
                  key={i}
                  onClick={() => handleGoToExercise(i)}
                  className={`w-2.5 h-2.5 rounded-full transition-all duration-300 cursor-pointer ${
                    exerciseStates[i]?.correct
                      ? 'bg-[#52C41A] shadow-sm hover:ring-2 hover:ring-[#52C41A]/30'
                      : exerciseStates[i]?.completed
                      ? 'bg-[#F39C11] shadow-sm hover:ring-2 hover:ring-[#F39C11]/30'
                      : i === currentIndex
                      ? 'bg-[#3498DB] shadow-sm animate-pulse ring-2 ring-[#3498DB]/30'
                      : 'bg-[#DCDFE6] hover:bg-[#C0C4CC]'
                  }`}
                  title={`题目 ${i + 1}${exerciseStates[i]?.correct ? ' (已通过)' : exerciseStates[i]?.completed ? ' (已尝试)' : ''}`}
                />
              ))}
            </div>
          </div>

          {/* Right: XP + Auto Save Status */}
          <div className="flex items-center gap-3">
            {autoSaveStatus !== 'idle' && (
              <div className={`auto-save-indicator ${autoSaveStatus === 'saving' ? 'saving' : ''}`}>
                <Save className="w-3 h-3" />
                {autoSaveStatus === 'saving' ? '保存中...' : '已保存'}
              </div>
            )}
            <div className="xp-badge flex items-center gap-1.5 px-3 py-1.5 rounded-full">
              <Zap className="w-4 h-4 text-[#F39C11]" />
              <span className="text-sm font-bold text-[#F39C11]">{xpEarned} XP</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - 两列独立滚动 */}
      <main className="flex-1 flex pt-[50px] h-[calc(100vh-50px)] overflow-hidden">
        {/* Left: Problem Panel - 40% - 独立滚动 */}
        <div className="w-[40%] ide-problem-panel bg-white flex-shrink-0" style={{ maxHeight: 'calc(100vh - 50px)', overflowY: 'auto', overflowX: 'hidden' }}>
          {currentExercise && (
            <div className="p-6">
              {/* Question header */}
              <div className="flex items-center gap-3 mb-6">
                <span className="px-4 py-1.5 bg-[#3498DB]/10 text-[#3498DB] rounded-lg text-sm font-semibold border border-[#3498DB]/20">
                  {currentIndex + 1} / {exercises.length}
                </span>
                <span className={`px-3 py-1 rounded-lg text-xs font-bold text-white difficulty-badge difficulty-${currentExercise.difficulty}`}>
                  {DIFFICULTY_NAMES[currentExercise.difficulty] || `难度 ${currentExercise.difficulty}`}
                </span>
              </div>

              {/* Title */}
              <h2 className="text-xl font-bold text-[#303133] mb-4 leading-relaxed">
                {currentExercise.content.title || currentExercise.content.text || '编程题'}
              </h2>

              {/* Description */}
              {currentExercise.content.description && (
                <div className="prose prose-sm max-w-none mb-6">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      h2: ({ children }) => (
                        <h3 className="text-base font-semibold text-[#303133] mt-4 mb-2 border-b border-[#E4E7ED] pb-2">{children}</h3>
                      ),
                      h3: ({ children }) => (
                        <h4 className="text-sm font-semibold text-[#303133] mt-3 mb-2">{children}</h4>
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
                      ul: ({ children }) => (
                        <ul className="list-disc list-inside text-[#606266] mb-2 space-y-1">{children}</ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="list-decimal list-inside text-[#606266] mb-2 space-y-1">{children}</ol>
                      ),
                    }}
                  >
                    {currentExercise.content.description}
                  </ReactMarkdown>
                </div>
              )}

              {/* Sample Input/Output Card */}
              {(currentExercise.content.sample_input || currentExercise.content.sample_output) && (
                <div className="mb-6">
                  <SampleIOCard
                    input={currentExercise.content.sample_input || ''}
                    output={currentExercise.content.sample_output || ''}
                    onRun={isProgramming ? handleSampleRun : undefined}
                    isRunning={isCustomRunning}
                  />
                </div>
              )}

              {/* Knowledge points */}
              {currentExercise.knowledge_points.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {currentExercise.knowledge_points.map((kp, i) => (
                    <span key={i} className="knowledge-tag px-3 py-1.5 text-[#3498DB] text-xs rounded-lg font-medium">
                      {kp}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Code Editor + Test Panel - 60% - 独立滚动 */}
        <div className="w-[60%] flex flex-col ide-editor-panel bg-white flex-shrink-0" style={{ maxHeight: 'calc(100vh - 50px)', overflow: 'hidden' }}>
          {isProgramming ? (
            <>
              {/* Tab Header - 固定 */}
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
                {/* 语言选择器 */}
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
                    language={LANGUAGE_MAP[language]?.monaco || 'cpp'}
                  />
                )}

                {rightPanelTab === 'test' && (
                  <div className="h-full overflow-y-auto p-4 bg-[#FAFBFC]">
                    <CustomTestInput
                      onRun={(input) => handleCustomRun(input, false)}  // 手动测试，不跳转
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
            </>
          ) : (
            <div className="flex-1 p-6 overflow-y-auto bg-[#FAFBFC]">
              <div className="space-y-3">
                {currentExercise?.content.options?.map((opt, i) => (
                  <button
                    key={i}
                    onClick={() => !submitted && setAnswer(opt)}
                    disabled={submitted}
                    className={`w-full p-4 rounded-lg border-2 text-left transition-all duration-200 ${
                      submitted
                        ? answer === opt
                          ? feedbackState === 'correct'
                            ? 'border-[#52C41A] bg-[#52C41A]/5'
                            : 'border-[#E74C3C] bg-[#E74C3C]/5'
                          : 'border-[#E4E7ED] bg-white opacity-60'
                        : answer === opt
                        ? 'border-[#3498DB] bg-[#3498DB]/5'
                        : 'border-[#E4E7ED] bg-white hover:border-[#3498DB]/50 hover:bg-[#F5F7FA]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold transition-colors ${
                        answer === opt && !submitted ? 'bg-[#3498DB] text-white' :
                        submitted && answer === opt && feedbackState === 'correct' ? 'bg-[#52C41A] text-white' :
                        submitted && answer === opt && feedbackState === 'wrong' ? 'bg-[#E74C3C] text-white' :
                        'bg-[#F5F7FA] text-[#606266]'
                      }`}>
                        {String.fromCharCode(65 + i)}
                      </span>
                      <span className="text-[#303133]">{opt}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Knowledge Check Modal */}
      <KnowledgeCheckModal
        isOpen={showKnowledgeCheck}
        questions={knowledgeCheckQuestions}
        onComplete={handleKnowledgeCheckComplete}
        onClose={() => {
          setShowKnowledgeCheck(false)
          setKnowledgeCheckQuestions([])
          setPendingNavigation(null)
        }}
      />

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
                {/* 上一题/下一题导航 */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrev}
                    disabled={currentIndex === 0}
                    className="p-2 rounded-lg border border-[#E4E7ED] text-[#606266] hover:bg-[#F5F7FA] hover:border-[#3498DB] hover:text-[#3498DB] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:border-[#E4E7ED] disabled:hover:text-[#606266] transition-colors"
                    title="上一题"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="text-sm text-[#606266] px-2">
                    {currentIndex + 1} / {exercises.length}
                  </span>
                  <button
                    onClick={handleNext}
                    disabled={currentIndex === exercises.length - 1}
                    className="p-2 rounded-lg border border-[#E4E7ED] text-[#606266] hover:bg-[#F5F7FA] hover:border-[#3498DB] hover:text-[#3498DB] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:border-[#E4E7ED] disabled:hover:text-[#606266] transition-colors"
                    title="下一题"
                  >
                    <ChevronRightIcon className="w-5 h-5" />
                  </button>
                </div>

                <div className="h-6 w-px bg-[#E4E7ED]" />

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-[#3498DB]/10 rounded-lg flex items-center justify-center border border-[#3498DB]/20">
                    <CheckCircle className="w-5 h-5 text-[#3498DB]" />
                  </div>
                  <div>
                    <p className="text-sm text-[#303133] font-medium">当前进度</p>
                    <p className="text-xs text-[#909399]">
                      已完成 {exerciseStates.filter(s => s?.completed).length} 题，正确 {exerciseStates.filter(s => s?.correct).length} 题
                    </p>
                  </div>
                </div>

                {isProgramming && testResults.length > 0 && (
                  <LuoguTestCasesSummary
                    passedCount={passedCount}
                    totalCount={testResults.length}
                  />
                )}
              </div>

              <div className="action-buttons-group">
                <button
                  onClick={handleSubmit}
                  disabled={(!isProgramming && !answer) || isSubmitting}
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
              <div className="flex items-center gap-4">
                {/* 上一题/下一题导航 */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrev}
                    disabled={currentIndex === 0}
                    className="p-2 rounded-lg border border-[#52C41A]/30 text-[#52C41A] hover:bg-[#52C41A]/10 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="上一题"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="text-sm text-[#52C41A] px-2 font-medium">
                    {currentIndex + 1} / {exercises.length}
                  </span>
                  <button
                    onClick={handleNext}
                    disabled={currentIndex === exercises.length - 1}
                    className="p-2 rounded-lg border border-[#52C41A]/30 text-[#52C41A] hover:bg-[#52C41A]/10 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="下一题"
                  >
                    <ChevronRightIcon className="w-5 h-5" />
                  </button>
                </div>

                <div className="h-6 w-px bg-[#52C41A]/20" />

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-[#52C41A]/10 rounded-lg flex items-center justify-center border border-[#52C41A]/20 success-pulse">
                    <CheckCircle className="w-6 h-6 text-[#52C41A]" />
                  </div>
                  <div>
                    <p className="font-semibold text-[#52C41A]">太棒了！</p>
                    {testResults.length > 0 && (
                      <p className="text-sm text-[#52C41A]/70">
                        全部 {testResults.length} 个测试点通过
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <div className="action-buttons-group">
                <button
                  onClick={handleStayOnCurrent}
                  className="btn-action btn-reset"
                >
                  留在该题
                </button>
                <button
                  onClick={isLastExercise ? handleStartVerificationFlow : handleNext}
                  className="btn-action btn-success"
                >
                  {isLastExercise ? '开始验证' : '下一题'}
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* 上一题/下一题导航 */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrev}
                    disabled={currentIndex === 0}
                    className="p-2 rounded-lg border border-[#E74C3C]/30 text-[#E74C3C] hover:bg-[#E74C3C]/10 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="上一题"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="text-sm text-[#E74C3C] px-2 font-medium">
                    {currentIndex + 1} / {exercises.length}
                  </span>
                  <button
                    onClick={handleNext}
                    disabled={currentIndex === exercises.length - 1}
                    className="p-2 rounded-lg border border-[#E74C3C]/30 text-[#E74C3C] hover:bg-[#E74C3C]/10 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="下一题"
                  >
                    <ChevronRightIcon className="w-5 h-5" />
                  </button>
                </div>

                <div className="h-6 w-px bg-[#E74C3C]/20" />

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-[#E74C3C]/10 rounded-lg flex items-center justify-center border border-[#E74C3C]/20 error-shake">
                    <XCircle className="w-6 h-6 text-[#E74C3C]" />
                  </div>
                  <div>
                    <p className="font-semibold text-[#E74C3C]">答案错误</p>
                    {testResults.length > 0 && (
                      <p className="text-sm text-[#E74C3C]/70">
                        通过 {passedCount}/{testResults.length} 个测试点
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <div className="action-buttons-group">
                <button
                  onClick={handleRetry}
                  className="btn-action btn-reset"
                >
                  <RotateCcw className="w-4 h-4" />
                  重试
                </button>
                {isProgramming && testResults.length > 0 && (
                  <button
                    onClick={() => setRightPanelTab('output')}
                    className="btn-action btn-submit"
                  >
                    查看详情
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
