'use client'

import { useParams } from 'next/navigation'
import {
  ArrowLeft,
  Clock,
  CheckCircle,
  Play,
  BookOpen,
  Loader2,
  ArrowRight,
} from 'lucide-react'
import { MasteryProgressBar } from '@/components/mastery/MasteryComponents'
import { useChapterData } from './hooks/use-chapter-data'
import { PageContainer, Grid, Panel, PanelHeader } from '@/components/layout'

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

  const remainingCount = sections.length - completedCount
  const totalMinutes = sections.reduce((sum, s) => sum + (s.estimated_minutes || 0), 0)

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
        <PageContainer className="py-4">
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
        </PageContainer>
      </header>

      {/* Content */}
      <main className="py-6 pb-12">
        <PageContainer>
          <Grid>
            {/* Main: progress + sections */}
            <div className="col-span-12 lg:col-span-8 space-y-6">
              <Panel>
                <PanelHeader title="学习进度" count={`${completedCount} / ${sections.length}`} />
                <div className="p-6">
                  <div className="h-2.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-[width] duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              </Panel>

              <Panel>
                <PanelHeader title="小节列表" count={`${sections.length} 个`} />
                <div>
                  {sections.map((section, index) => (
                    <button type="button"
                      key={section.id}
                      onClick={() => handleSelectSection(section.id)}
                      className="w-full px-6 py-5 border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors text-left group"
                    >
                      <div className="flex items-start gap-4">
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

                  {sections.length === 0 && (
                    <div className="text-center py-12">
                      <BookOpen strokeWidth={1.5} className="size-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">该章节暂无小节内容</p>
                    </div>
                  )}
                </div>
              </Panel>
            </div>

            {/* Side: chapter overview */}
            <aside className="col-span-12 lg:col-span-4 space-y-6">
              <Panel>
                <PanelHeader title="章节概览" />
                <div className="p-6 space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-muted p-4">
                      <p className="text-2xl font-bold text-foreground">{sections.length}</p>
                      <p className="text-xs text-muted-foreground mt-1">小节总数</p>
                    </div>
                    <div className="bg-muted p-4">
                      <p className="text-2xl font-bold text-emerald-600">{completedCount}</p>
                      <p className="text-xs text-muted-foreground mt-1">已完成</p>
                    </div>
                    <div className="bg-muted p-4">
                      <p className="text-2xl font-bold text-foreground">{remainingCount}</p>
                      <p className="text-xs text-muted-foreground mt-1">待学习</p>
                    </div>
                    <div className="bg-muted p-4">
                      <p className="text-2xl font-bold text-foreground">{totalMinutes}</p>
                      <p className="text-xs text-muted-foreground mt-1">预计分钟</p>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-border">
                    <p className="text-sm text-muted-foreground mb-4">
                      完成全部小节后，可通过基础测试检验掌握情况。
                    </p>
                    <button type="button"
                      onClick={() => sections.length > 0 && handleSelectSection(sections[0].id)}
                      disabled={sections.length === 0}
                      className="w-full flex items-center justify-center gap-2 py-3 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                      开始学习
                      <ArrowRight strokeWidth={1.5} className="size-4" />
                    </button>
                  </div>
                </div>
              </Panel>
            </aside>
          </Grid>
        </PageContainer>
      </main>
    </div>
  )
}
