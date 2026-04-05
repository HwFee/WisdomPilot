'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useParams, useSearchParams } from 'next/navigation'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { getStoredUser, getStoredToken, logout, User, startLearningSession, endLearningSession, updateSessionSubsection, updateChapterProgress, getUserProgress, ChapterProgress, getChapterExerciseAnswers, ChapterExerciseAnswers } from '@/lib/api'
import { courseChapters, CourseChapter } from '@/lib/course-data'
import { ChapterHeader, ChapterSidebar, ChapterContent } from '@/components/layout'
import { CodeEditorPanel, CodeEditorPanelRef } from '@/components/editor/CodeEditorPanel'

const CONTENT_TRANSITION = {
  duration: 0.32,
  ease: [0.22, 1, 0.36, 1] as const,
}

const PANEL_TRANSITION = {
  duration: 0.34,
  ease: [0.22, 1, 0.36, 1] as const,
}

const IDE_WIDTH = 50 // percentage

export default function ChapterPage() {
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
  const sessionIdRef = useRef<string | null>(null)
  const sessionStartedAtRef = useRef<number | null>(null)
  const tokenRef = useRef<string | null>(null)
  const codeEditorRef = useRef<CodeEditorPanelRef>(null)

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
    completedCount: number,
    totalCount: number
  ) => {
    if (!chapter || !tokenRef.current) {
      return
    }
    try {
      const result = await updateChapterProgress(tokenRef.current, chapter.id, {
        completed_exercise_count: completedCount,
        total_exercises: totalCount,
        completed_exercises_by_subsection: completedExercisesBySubsection,
      })
      setChapterProgress(result)
    } catch (error) {
      console.error('[进度] 保存习题完成失败:', error)
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

  const handleStartIDEWithTemplate = (template: string) => {
    setProgrammingTemplate(template)
    setIsSplitScreen(true)
    setTimeout(() => {
      codeEditorRef.current?.setCode(template)
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
                  onClose={handleSplitScreen}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}
