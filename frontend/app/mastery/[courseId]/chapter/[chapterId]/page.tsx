'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Clock, CheckCircle, Play, BookOpen, Loader2, Target } from 'lucide-react'
import { getChapterSections, type SectionSummary } from '@/lib/api/sections'
import { getStoredToken } from '@/lib/api'
import { MasteryProgressBar } from '@/components/mastery/MasteryComponents'

interface ChapterInfo {
  id: number
  title: string
  course_id: number
  course_name: string
}

export default function ChapterSectionsPage() {
  const params = useParams()
  const { push } = useRouter()
  const courseId = parseInt(params.courseId as string)
  const chapterId = parseInt(params.chapterId as string)

  const [sections, setSections] = useState<SectionSummary[]>([])
  const [chapterInfo, setChapterInfo] = useState<ChapterInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSections()
  }, [chapterId])

  const loadSections = async () => {
    const token = getStoredToken()
    if (!token) {
      push('/login')
      return
    }

    try {
      setLoading(true)
      const response = await getChapterSections(chapterId, token)
      setSections(response.sections)

      // 调试日志：显示小节掌握度数据
      response.sections.forEach((s, i) => {
      })

      // 从第一个section获取章节信息（如果有的话）
      // 或者调用单独的API获取章节信息
      // 这里暂时从localStorage获取
      const stored = localStorage.getItem('current_chapter_info:v1')
      if (stored) {
        setChapterInfo(JSON.parse(stored))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectSection = (section: SectionSummary) => {
    // 跳转到小节学习页面（带章节信息）
    push(`/mastery/${courseId}/chapter/${chapterId}/section/${section.id}`)
  }

  const handleBack = () => {
    push(`/mastery/${courseId}`)
  }

  const completedCount = sections.filter(s => s.is_completed).length
  const progress = sections.length > 0 ? Math.round((completedCount / sections.length) * 100) : 0

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <button type="button" onClick={handleBack} className="text-primary hover:underline">
            返回章节列表
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b">
        <div className="max-w-4xl mx-auto p-4">
          <div className="flex items-center gap-4">
            <button type="button"
              onClick={handleBack}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ArrowLeft className="size-5" />
            </button>
            <div className="flex-1 min-w-0">
              <h1 className="text-lg font-semibold text-foreground truncate">
                {chapterInfo?.title || `第${chapterId}章`}
              </h1>
              <p className="text-sm text-muted-foreground">
                {chapterInfo?.course_name || '选择小节开始学习'}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Overview */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-card rounded-xl border p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <BookOpen className="size-5 text-primary" />
              <span className="font-medium">学习进度</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {completedCount} / {sections.length} 小节已完成
            </span>
          </div>
          <div className="h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Section List */}
        <div className="flex flex-col gap-y-3">
          {sections.map((section, index) => (
            <button type="button"
              key={section.id}
              onClick={() => handleSelectSection(section)}
              className="w-full bg-card rounded-xl border p-4 hover:border-primary/50 hover:shadow-sm transition-all text-left group"
            >
              <div className="flex items-start gap-4">
                {/* Order indicator */}
                <div className={`flex-shrink-0 size-10 rounded-lg flex items-center justify-center text-sm font-medium ${
                  section.is_completed
                    ? 'bg-green-500/20 text-green-600 dark:text-green-400'
                    : 'bg-primary/10 text-primary'
                }`}>
                  {section.is_completed ? (
                    <CheckCircle className="size-5" />
                  ) : (
                    index + 1
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <h3 className="font-medium text-foreground group-hover:text-primary transition-colors">
                        {section.title}
                      </h3>
                      {section.description && (
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {section.description}
                        </p>
                      )}
                    </div>
                    <Play className="size-5 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0 mt-1" />
                  </div>

                  {/* Meta info */}
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="size-3.5" />
                      {section.estimated_minutes} 分钟
                    </span>
                    {section.is_completed && (
                      <span className="text-green-600 dark:text-green-400">
                        已完成
                      </span>
                    )}
                  </div>

                  {/* Mastery Progress Bar - 始终显示 */}
                  <div className="mt-3">
                    <MasteryProgressBar
                      score={section.mastery_score ?? 0}
                      size="sm"
                      showLabel={true}
                    />
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {sections.length === 0 && (
          <div className="text-center py-12">
            <BookOpen className="size-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">该章节暂无小节内容</p>
          </div>
        )}
      </div>
    </div>
  )
}
