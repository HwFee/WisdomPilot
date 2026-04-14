'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useParams, useSearchParams } from 'next/navigation'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { getStoredUser, getStoredToken, logout, User, startLearningSession, endLearningSession, updateSessionSubsection, updateChapterProgress, getUserProgress, ChapterProgress, getChapterExerciseAnswers, ChapterExerciseAnswers } from '@/lib/api'
import { courseChapters, CourseChapter, getChapterTotalExercises } from '@/lib/course-data'
import { ChapterHeader, ChapterSidebar, ChapterContent } from '@/components/layout'
import { CodeEditorPanel, CodeEditorPanelRef } from '@/components/editor/CodeEditorPanel'
import { AIContextProvider } from '@/contexts/AIContext'
import { MorphPanel } from '@/components/ui/morph-panel'

const CONTENT_TRANSITION = {
  duration: 0.32,
  ease: [0.22, 1, 0.36, 1] as const,
}

const PANEL_TRANSITION = {
  duration: 0.34,
  ease: [0.22, 1, 0.36, 1] as const,
}

const IDE_WIDTH = 50 // percentage

export default function ChapterPageContent() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lang, setLang] = useState<'zh' | 'en'>('zh')
  const [chapter, setChapter] = useState<CourseChapter | null>(null)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [activeIndex, setActiveIndex] = useState(0)
  const [isSplitScreen, setIsSplitScreen] = useState(false)
  const [chapterProgress, setChapterProgress] = useState<ChapterProgress | null>(null)
  const [exerciseAnswers, setExerciseAnswers] = useState<ChapterExerciseAnswers | null>(null)
  const [programmingTemplate, setProgrammingTemplate] = useState('')
  const [programmingQuestion, setProgrammingQuestion] = useState('')
  const [programmingOptions, setProgrammingOptions] = useState<string[] | undefined>(undefined)
  const [programmingResults, setProgrammingResults] = useState<Record<number, 'correct' | 'wrong'>>({})
  // Sync programmingResults from chapterProgress.exercise_results when progress changes
  useEffect(() => {
    if (!chapterProgress?.exercise_results || !chapter) return
    // exercise_results key format: "chapterId-subsectionIndex-exerciseId"
    const results: Record<number, 'correct' | 'wrong'> = {}
    let hasMatchingResult = false
    for (const [key, status] of Object.entries(chapterProgress.exercise_results)) {
      const parts = key.split('-')
      if (parts.length !== 3) continue
      const [cId, sIdx, eId] = parts.map(Number)
      if (cId === chapter.id && sIdx === activeIndex && eId === 0) {
        results[0] = status as 'correct' | 'wrong'
        hasMatchingResult = true
      }
    }
    if (hasMatchingResult) {
      setProgrammingResults(prev => ({ ...prev, ...results }))
    } else {
      // 如果没有匹配的结果，清除编程题结果
      setProgrammingResults(prev => {
        const newResults = { ...prev }
        delete newResults[0]
        return newResults
      })
    }
  }, [chapterProgress?.exercise_results, chapter, activeIndex])
  const sessionIdRef = useRef<string | null>(null)
  const sessionStartedAtRef = useRef<number | null>(null)
  const tokenRef = useRef<string | null>(null)
  const codeEditorRef = useRef<CodeEditorPanelRef>(null)
  const isDebug = searchParams.get('debug') === '1'

  const prefersReducedMotion = useReducedMotion()

  useEffect(() => {
    const token = getStoredToken()
    const storedUser = getStoredUser()
    const savedLang = localStorage.getItem('language') || 'zh'

    if (!token || !storedUser) {
      router.push('/login')
      return
    }

    setUser(storedUser)
    setLang(savedLang as 'zh' | 'en')
    setIsLoading(false)
  }, [router])

  // Clear programming template when subsection changes
  useEffect(() => {
    setProgrammingTemplate('')
  }, [activeIndex])

  useEffect(() => {
    if (params.id) {
      const chapterId = parseInt(params.id as string, 10)
      const foundChapter = courseChapters.find(c => c.id === chapterId)
      setChapter(foundChapter || null)
      setActiveIndex(0)
    }
  }, [params.id])

  // Fetch chapter progress when chapter changes
  useEffect(() => {
    if (!chapter) return
    const token = getStoredToken()
    if (!token) return

    const fetchProgress = async () => {
      try {
        const allProgress = await getUserProgress(token)
        const progress = allProgress.find((p: ChapterProgress) => p.chapter_id === chapter.id)
        setChapterProgress(progress || null)
      } catch (error) {
        console.error('[进度] 获取章节进度失败:', error)
      }
    }

    fetchProgress()
  }, [chapter])

  // Fetch chapter exercise answers (for choice question grading)
  useEffect(() => {
    if (!chapter) return
    const token = getStoredToken()
    if (!token) return

    const fetchAnswers = async () => {
      try {
        const answers = await getChapterExerciseAnswers(token, chapter.id)
        setExerciseAnswers(answers)
      } catch (error) {
        console.error('[答案] 获取章节习题答案失败:', error)
      }
    }

    fetchAnswers()
  }, [chapter])

  // Handle exercise completion
  const handleExerciseComplete = async (
    completedExercisesBySubsection: Record<number, number[]>,
    _completedCount: number,
    _totalCount: number
  ) => {
    if (!chapter || !tokenRef.current) {
      return
    }
    try {
      // Merge with existing completed exercises
      const existingCompletedBySubsection = chapterProgress?.completed_exercises_by_subsection || {}
      const mergedCompletedBySubsection: Record<number, number[]> = { ...existingCompletedBySubsection }
      for (const [subsectionIdx, exerciseIds] of Object.entries(completedExercisesBySubsection)) {
        const idx = parseInt(subsectionIdx, 10)
        const existing = mergedCompletedBySubsection[idx] || []
        // Merge and dedupe exercise IDs
        const merged = Array.from(new Set([...existing, ...exerciseIds]))
        mergedCompletedBySubsection[idx] = merged
      }

      // Calculate total completed exercises from merged dict
      const totalCompleted = Object.values(mergedCompletedBySubsection).reduce(
        (sum, exerciseIds) => sum + exerciseIds.length,
        0
      )
      const totalExercises = getChapterTotalExercises(chapter)

      const result = await updateChapterProgress(tokenRef.current, chapter.id, {
        completed_exercise_count: totalCompleted,
        total_exercises: totalExercises,
        completed_exercises_by_subsection: mergedCompletedBySubsection,
      })
      setChapterProgress(result)
    } catch (error) {
      console.error('[进度] 保存习题完成失败:', error)
    }
  }

  // Handle programming exercise result (correct/wrong)
  const handleProgrammingResult = (isCorrect: boolean, exerciseId: number = 0) => {
    setProgrammingResults(prev => ({ ...prev, [exerciseId]: isCorrect ? 'correct' : 'wrong' }))
  }

  // Handle programming exercise attempt - auto-save result to backend
  const handleProgrammingAttempt = async (isCorrect: boolean, exerciseId: number = 0) => {
    if (!tokenRef.current || !chapter) return
    try {
      // Construct exercise key: chapterId-subsectionIndex-exerciseId
      const exerciseKey = `${chapter.id}-${activeIndex}-${exerciseId}`
      const resultStatus = isCorrect ? 'correct' : 'wrong'

      // Get existing exercise results
      const existingResults = chapterProgress?.exercise_results || {}

      // Update with new result
      const updatedResults = { ...existingResults, [exerciseKey]: resultStatus }

      // Save to backend
      await updateChapterProgress(tokenRef.current, chapter.id, {
        exercise_results: updatedResults,
      })
    } catch (error) {
      console.error('[编程题] 保存答题结果失败:', error)
    }
  }

  // Handle choice exercise attempt - auto-save result to backend
  const handleChoiceAttempt = async (isCorrect: boolean, exerciseId: number) => {
    if (!tokenRef.current || !chapter) return
    try {
      // Construct exercise key: chapterId-subsectionIndex-exerciseId
      const exerciseKey = `${chapter.id}-${activeIndex}-${exerciseId}`
      const resultStatus = isCorrect ? 'correct' : 'wrong'

      // Get existing exercise results
      const existingResults = chapterProgress?.exercise_results || {}

      // Update with new result
      const updatedResults = { ...existingResults, [exerciseKey]: resultStatus }

      // Save to backend
      await updateChapterProgress(tokenRef.current, chapter.id, {
        exercise_results: updatedResults,
      })
    } catch (error) {
      console.error('[选择题] 保存答题结果失败:', error)
    }
  }

  // Debug: reset chapter progress directly in database
  const handleResetProgress = async () => {
    if (!tokenRef.current || !chapter) return
    try {
      const totalExercises = getChapterTotalExercises(chapter)
      const result = await updateChapterProgress(tokenRef.current, chapter.id, {
        completed_exercise_count: 0,
        total_exercises: totalExercises,
        completed_exercises_by_subsection: {},
        exercise_results: {},
      })
      setProgrammingResults({})
      setChapterProgress(result)
      alert('已重置答题状态')
    } catch (error) {
      console.error('[Debug] 重置答题状态失败:', error)
      alert('重置失败')
    }
  }

  // Start learning session when chapter is loaded
  useEffect(() => {
    const token = getStoredToken()
    tokenRef.current = token
    if (!chapter || !token) return

    const startSession = async () => {
      try {
        const session = await startLearningSession(token, chapter.id, activeIndex)
        sessionIdRef.current = session.id
        sessionStartedAtRef.current = Date.now()
      } catch (error) {
        console.error('[会话] 开始会话失败:', error)
      }
    }

    startSession()

    let sessionEnded = false
    const endSession = async () => {
      if (sessionEnded || !sessionIdRef.current || !sessionStartedAtRef.current) {
        return
      }
      sessionEnded = true
      const duration = Math.floor((Date.now() - sessionStartedAtRef.current) / 1000)
      try {
        await endLearningSession(tokenRef.current!, duration)
      } catch (error) {
        console.error('[会话] 结束会话失败:', error)
      }
    }

    window.addEventListener('beforeunload', endSession)
    return () => {
      window.removeEventListener('beforeunload', endSession)
      endSession()
    }
  }, [chapter])

  // Handle subsection query param
  useEffect(() => {
    const subsectionParam = searchParams.get('subsection')
    if (subsectionParam) {
      const idx = parseInt(subsectionParam, 10)
      if (!isNaN(idx) && idx >= 0) {
        setActiveIndex(idx)
      }
    }
  }, [searchParams])

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const toggleLanguage = () => {
    const newLang = lang === 'zh' ? 'en' : 'zh'
    setLang(newLang)
    localStorage.setItem('language', newLang)
  }

  const handleToggleSidebar = () => {
    setIsSidebarOpen(prev => !prev)
  }

  const handleSplitScreen = () => {
    setIsSplitScreen(prev => !prev)
  }

  const handleStartIDEWithTemplate = (template: string, question = '', options?: string[], subsectionIndex?: number) => {
    // Check if there's saved code in localStorage (across all languages)
    const chapterId = parseInt(params.id as string, 10)
    const subIdx = subsectionIndex ?? 0
    const languages = [71, 63, 74, 50, 54] // Python, JavaScript, TypeScript, C, C++
    let savedCode: string | null = null
    for (const langId of languages) {
      savedCode = localStorage.getItem(`code_${chapterId}_${subIdx}_${langId}`)
      if (savedCode) break
    }
    const initialCode = savedCode || template

    setProgrammingTemplate(initialCode)
    setProgrammingQuestion(question)
    setProgrammingOptions(options)
    setIsSplitScreen(true)
    setTimeout(() => {
      codeEditorRef.current?.setCode(initialCode)
    }, 100)
  }

  const handleSelectSubsection = (index: number) => {
    setActiveIndex(index)
    const token = getStoredToken()
    if (token && sessionIdRef.current) {
      updateSessionSubsection(token, index).catch(err => {
        console.error('[切换小节] 更新失败:', err)
      })
    }
  }

  const handleNavigate = (index: number) => {
    setActiveIndex(index)
    const token = getStoredToken()
    if (token && sessionIdRef.current) {
      updateSessionSubsection(token, index).catch(err => {
        console.error('[切换小节] 更新失败:', err)
      })
    }
  }

  const handleBack = () => {
    router.push('/dashboard')
  }

  // Calculate sidebar offset for main content
  const sidebarOffset = isSidebarOpen ? 288 : 64

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500">加载中...</p>
      </div>
    )
  }

  if (!chapter) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <p className="text-gray-500 mb-4">章节未找到</p>
        <button
          onClick={() => router.push('/dashboard')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          返回仪表盘
        </button>
      </div>
    )
  }

  return (
    <AIContextProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <ChapterHeader
          chapter={chapter}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={handleToggleSidebar}
          user={user}
          onLogout={handleLogout}
          onToggleLang={toggleLanguage}
          lang={lang}
        />

        {/* Debug button - only visible when ?debug=1 */}
        {isDebug && chapter?.id === 1 && (
          <button
            onClick={handleResetProgress}
            className="fixed bottom-4 right-4 px-3 py-1.5 bg-red-500 text-white text-xs rounded-lg shadow-lg hover:bg-red-600 transition-colors z-50"
          >
            [Debug] 重置答题状态
          </button>
        )}

        {/* Sidebar */}
        <ChapterSidebar
          chapter={chapter}
          isOpen={isSidebarOpen}
          activeIndex={activeIndex}
          onSelectSubsection={handleSelectSubsection}
          lang={lang}
        />

        {/* Main Content */}
        <motion.div
          className="pt-14 min-h-screen"
          animate={{
            paddingLeft: sidebarOffset,
          }}
          transition={prefersReducedMotion ? { duration: 0.05 } : CONTENT_TRANSITION}
        >
          {/* Split screen layout */}
          <div className="flex h-[calc(100vh-56px)]">
            {/* Left: Course Content */}
            <motion.div
              className="min-h-0 flex-1 overflow-hidden min-w-0"
              animate={{
                width: isSplitScreen ? `${100 - IDE_WIDTH}%` : '100%',
              }}
              transition={prefersReducedMotion ? { duration: 0.05 } : CONTENT_TRANSITION}
            >
              <ChapterContent
                chapter={chapter}
                activeIndex={activeIndex}
                onNavigate={handleNavigate}
                onStartIDE={handleSplitScreen}
                onStartIDEWithTemplate={handleStartIDEWithTemplate}
                isSplitScreen={isSplitScreen}
                lang={lang}
                completedExercisesBySubsection={chapterProgress?.completed_exercises_by_subsection || {}}
                onExerciseComplete={handleExerciseComplete}
                onProgrammingResult={handleProgrammingResult}
                onChoiceAttempt={handleChoiceAttempt}
                programmingResults={programmingResults}
                exerciseAnswers={exerciseAnswers?.answers || []}
              />
            </motion.div>

            {/* Right: IDE Panel with AnimatePresence */}
            <AnimatePresence mode="wait">
              {isSplitScreen && (
                <motion.div
                  key="ide-panel"
                  className="border-l border-gray-200 flex flex-col min-w-0 overflow-hidden"
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: `${IDE_WIDTH}%`, opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  transition={prefersReducedMotion ? { duration: 0.05 } : PANEL_TRANSITION}
                >
                  <CodeEditorPanel
                    ref={codeEditorRef}
                    defaultCode={programmingTemplate}
                    defaultLanguage={71}
                    chapterId={chapter.id}
                    subsectionIndex={activeIndex}
                    exerciseQuestion={programmingQuestion || '编程题'}
                    exerciseOptions={programmingOptions}
                    onClose={handleSplitScreen}
                    onExerciseComplete={handleExerciseComplete}
                    onProgrammingResult={handleProgrammingResult}
                    onProgrammingAttempt={handleProgrammingAttempt}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* AI Buddy (floating) */}
        <MorphPanel />
      </div>
    </AIContextProvider>
  )
}
