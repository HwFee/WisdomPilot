'use client'

import { useParams } from 'next/navigation'
import {
  ArrowLeft,
  Clock,
  CheckCircle,
  Play,
  BookOpen,
  Loader2,
} from 'lucide-react'
import { MasteryProgressBar } from '@/components/mastery/MasteryComponents'
import { useChapterData } from './hooks/use-chapter-data'

export default function ChapterSectionsPage() {
  const params = useParams()
  const courseId = parseInt(params.courseId as string)
  const chapterId = parseInt(params.chapterId as string)

  const {
    sections,
    chapterInfo,
    loading,
    error,
    completedCount,
    progress,
    handleSelectSection,
    handleBack,
  } = useChapterData(courseId, chapterId)

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 strokeWidth={1.5} className="size-8 text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
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
      <header className="sticky top-0 z-50 bg-background border-b">
        <div className="max-w-4xl mx-auto p-4">
          <div className="flex items-center gap-4">
            <button type="button"
              onClick={handleBack}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ArrowLeft strokeWidth={1.5} className="size-5" />
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
        <div className="bg-card rounded-lg border p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <BookOpen strokeWidth={1.5} className="size-5 text-primary" />
              <span className="font-medium">学习进度</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {completedCount} / {sections.length} 小节已完成
            </span>
          </div>
          <div className="h-2.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-[width] duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Section List */}
        <div className="flex flex-col gap-y-3">
          {sections.map((section, index) => (
            <button type="button"
              key={section.id}
              onClick={() => handleSelectSection(section.id)}
              className="w-full bg-card rounded-lg border p-4 hover:border-primary hover:bg-muted transition-colors text-left group"
            >
              <div className="flex items-start gap-4">
                {/* Order indicator */}
                <div className={`flex-shrink-0 size-10 rounded-lg flex items-center justify-center text-sm font-medium ${
                  section.is_completed
                    ? 'bg-secondary text-emerald-600 dark:text-emerald-400'
                    : 'bg-secondary text-primary'
                }`}>
                  {section.is_completed ? (
                    <CheckCircle strokeWidth={1.5} className="size-5" />
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
                    <Play strokeWidth={1.5} className="size-5 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0 mt-1" />
                  </div>

                  {/* Meta info */}
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock strokeWidth={1.5} className="size-3.5" />
                      {section.estimated_minutes} 分钟
                    </span>
                    {section.is_completed && (
                      <span className="text-emerald-600 dark:text-emerald-400">
                        已完成
                      </span>
                    )}
                  </div>

                  {/* Mastery Progress Bar */}
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
            <BookOpen strokeWidth={1.5} className="size-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">该章节暂无小节内容</p>
          </div>
        )}
      </div>
    </div>
  )
}
