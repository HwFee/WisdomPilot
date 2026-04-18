'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Clock, BookOpen, CheckCircle, Play, Loader2, ArrowRight } from 'lucide-react'
import { getSection, saveSectionProgress, type SectionDetail } from '@/lib/api/sections'
import { getStoredToken } from '@/lib/api'
import { startLearningSession, endLearningSessionKeepalive } from '@/lib/api/stats'

export default function SectionLearningPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = parseInt(params.courseId as string)
  const sectionId = parseInt(params.sectionId as string)

  const [section, setSection] = useState<SectionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // 学习时长统计
  const sessionStartedAtRef = useRef<number | null>(null)
  const sessionInitializedRef = useRef(false)
  const sessionEndedRef = useRef(false)
  const chapterIdRef = useRef<number | null>(null)

  useEffect(() => {
    loadSection()
  }, [sectionId])

  // 开始学习会话
  const startTrackedSession = useCallback(async (chapterId: number) => {
    const token = getStoredToken()
    if (!token || sessionInitializedRef.current) return

    try {
      await startLearningSession(token, chapterId, 0)
      const now = Date.now()
      sessionStartedAtRef.current = now
      sessionInitializedRef.current = true
      sessionEndedRef.current = false
      chapterIdRef.current = chapterId
    } catch {
      // Session start failed - will retry on next interaction
    }
  }, [])

  // 结束学习会话
  const endTrackedSession = useCallback(() => {
    if (sessionEndedRef.current) {
      return
    }

    const token = getStoredToken()
    const startedAt = sessionStartedAtRef.current

    if (!token || !startedAt || !sessionInitializedRef.current) {
      return
    }

    const durationSeconds = Math.max(
      1,
      Math.floor((Date.now() - startedAt) / 1000),
    )

    sessionEndedRef.current = true
    sessionInitializedRef.current = false
    sessionStartedAtRef.current = null

    endLearningSessionKeepalive(token, durationSeconds, chapterIdRef.current ?? undefined)
  }, [])

  // 当 section 加载完成后启动会话
  useEffect(() => {
    if (section && !sessionInitializedRef.current) {
      startTrackedSession(section.chapter_id)
    }
  }, [section, startTrackedSession])

  // 使用 isMountedRef 来区分 StrictMode 的假 unmount 和真正的 unmount
  const isMountedRef = useRef(false)

  useEffect(() => {
    isMountedRef.current = true

    return () => {
      isMountedRef.current = false

      requestAnimationFrame(() => {
        if (!isMountedRef.current) {
          endTrackedSession()
        }
      })
    }
  }, [endTrackedSession])

  const loadSection = async () => {
    const token = getStoredToken()
    if (!token) {
      router.push('/login')
      return
    }

    try {
      setLoading(true)
      const response = await getSection(sectionId, token)
      setSection(response.section)

      // 自动保存进度为 content（正在学习中）
      if (response.section.last_position === 'content' && !response.section.is_completed) {
        await saveSectionProgress(sectionId, 'content', false, token)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleStartQuiz = async () => {
    const token = getStoredToken()
    if (!token) return

    // 保存会话开始时间到 localStorage，让做题页面继续使用
    if (sessionStartedAtRef.current && sessionInitializedRef.current) {
      const sessionData = {
        startedAt: sessionStartedAtRef.current,
        chapterId: chapterIdRef.current,
        fromSection: sectionId
      }
      localStorage.setItem('masterySession', JSON.stringify(sessionData))

      // 标记会话已转移，不要在本页面结束
      sessionEndedRef.current = true
    }

    try {
      setSaving(true)
      await saveSectionProgress(sectionId, 'quiz', false, token)

      if (section) {
        router.push(`/mastery/${courseId}?chapter=${section.chapter_id}&skip=1&fromSection=${sectionId}&continueSession=1`)
      }
    } catch {
      // Progress save failed - continue anyway
    } finally {
      setSaving(false)
    }
  }

  const handleBack = () => {
    // 返回小节选择页面
    if (section) {
      router.push(`/mastery/${courseId}/chapter/${section.chapter_id}`)
    } else {
      router.push(`/mastery/${courseId}`)
    }
  }

  // 简单的Markdown渲染（实际项目应该用markdown库）
  const renderMarkdown = (content: string) => {
    // 简单处理：代码块、标题、段落
    return content
      .split('\n')
      .map((line, index) => {
        // 代码块
        if (line.startsWith('```')) {
          return null // 简化处理
        }
        // 标题
        if (line.startsWith('### ')) {
          return <h3 key={index} className="text-lg font-semibold mt-6 mb-3">{line.slice(4)}</h3>
        }
        if (line.startsWith('## ')) {
          return <h2 key={index} className="text-xl font-semibold mt-8 mb-4">{line.slice(3)}</h2>
        }
        if (line.startsWith('# ')) {
          return <h1 key={index} className="text-2xl font-bold mt-8 mb-4">{line.slice(2)}</h1>
        }
        // 列表
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return <li key={index} className="ml-4 mb-1">{line.slice(2)}</li>
        }
        if (line.match(/^\d+\.\s/)) {
          const match = line.match(/^\d+\.\s(.*)/)
          return <li key={index} className="ml-4 mb-1 list-decimal">{match?.[1] || ''}</li>
        }
        // 空行
        if (line.trim() === '') {
          return <br key={index} />
        }
        // 普通段落
        return <p key={index} className="mb-3 leading-relaxed">{line}</p>
      })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !section) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error || '未找到小节'}</p>
          <button onClick={handleBack} className="text-primary hover:underline">
            返回
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={handleBack}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex-1 min-w-0">
              <h1 className="text-lg font-semibold text-foreground truncate">
                {section.title}
              </h1>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {section.estimated_minutes} 分钟
                </span>
                {section.is_completed && (
                  <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                    <CheckCircle className="w-3.5 h-3.5" />
                    已完成
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-6 pb-32">
        {/* Learning Objectives */}
        {section.learning_objectives && section.learning_objectives.length > 0 && (
          <div className="bg-primary/5 rounded-xl border border-primary/20 p-4 mb-6">
            <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-primary" />
              学习目标
            </h2>
            <ul className="space-y-2">
              {section.learning_objectives.map((objective, index) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                  <span>{objective}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Description */}
        {section.description && (
          <p className="text-muted-foreground mb-6 text-lg">
            {section.description}
          </p>
        )}

        {/* Main Content */}
        <div ref={contentRef} className="prose prose-slate dark:prose-invert max-w-none">
          {section.content ? (
            <div className="text-foreground leading-relaxed">
              {renderMarkdown(section.content)}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>内容正在编写中...</p>
            </div>
          )}
        </div>
      </main>

      {/* Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-t">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <button
            onClick={handleStartQuiz}
            disabled={saving}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium bg-gradient-to-r from-primary to-primary/80 text-white hover:shadow-lg transition-all disabled:opacity-70"
          >
            {saving ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Play className="w-5 h-5" />
                开始测试
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
