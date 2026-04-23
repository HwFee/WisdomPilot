'use client'

import Link from 'next/link'
import { Code2, ArrowRight, BookOpen } from 'lucide-react'

interface Course {
  id: number
  name: string
  progress: number
  color: string
}

interface RecommendedCourse {
  id: number
  name: string
  color: string
  description?: string
}

interface MyCoursesGridProps {
  courses: Course[]
  recommendedCourses?: RecommendedCourse[]
  onSelectCourse: (courseId: number) => void
  lang?: 'zh' | 'en'
  compact?: boolean
}

export function MyCoursesGrid({ courses, recommendedCourses = [], onSelectCourse, lang = 'zh', compact = false }: MyCoursesGridProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  // 空状态 + 推荐课程
  if (courses.length === 0) {
    return (
      <div className="bg-card rounded-2xl border border-border p-6 h-full flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-foreground flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary" />
            {t('正在学习', 'Learning')}
          </h3>
          <Link href="/courses" className="text-sm text-primary hover:text-primary/80 transition-colors">
            {t('+ 浏览课程', '+ Browse Courses')}
          </Link>
        </div>

        <div className="flex-1 flex flex-col justify-center">
          {/* 推荐课程 */}
          {recommendedCourses.length > 0 ? (
            <>
              <p className="text-sm text-muted-foreground mb-4">{t('推荐课程', 'Recommended Courses')}</p>
              <div className="grid grid-cols-2 gap-3">
                {recommendedCourses.slice(0, 4).map((course) => (
                  <button type="button"
                    key={course.id}
                    onClick={() => onSelectCourse(course.id)}
                    className="group p-4 rounded-xl bg-muted/30 hover:bg-muted/50 border border-border/50 hover:border-primary/30 text-left transition-all"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: `${course.color}20` }}
                      >
                        <Code2 className="w-4 h-4" style={{ color: course.color }} />
                      </div>
                      <span className="font-medium text-foreground text-sm group-hover:text-primary transition-colors truncate">
                        {course.name}
                      </span>
                    </div>
                    {course.description && (
                      <p className="text-xs text-muted-foreground truncate">{course.description}</p>
                    )}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-6">
              <BookOpen className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">{t('暂无课程', 'No courses yet')}</p>
              <p className="text-sm text-muted-foreground">{t('选择一门课程开始学习吧', 'Select a course to start')}</p>
              <Link href="/courses" className="inline-flex items-center gap-1 mt-3 text-primary hover:underline">
                {t('浏览全部课程', 'Browse All Courses')}
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-card rounded-2xl border border-border p-6 h-full flex flex-col ${compact ? 'overflow-hidden' : ''}`}>
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <h3 className="font-semibold text-foreground flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary" />
          {t('正在学习', 'Learning')}
          <span className="text-muted-foreground">({courses.length})</span>
        </h3>
        <Link href="/courses" className="text-sm text-primary hover:text-primary/80 transition-colors">
          {t('+ 浏览更多', '+ More')}
        </Link>
      </div>

      <div className="flex-1 overflow-auto">
        <div className={`grid ${compact ? 'grid-cols-1 gap-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4'}`}>
          {courses.map((course) => (
            <div
              key={course.id}
              onClick={() => onSelectCourse(course.id)}
              className="group p-4 rounded-xl bg-muted/30 hover:bg-muted/50 border border-border/50 hover:border-primary/30 cursor-pointer transition-all"
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${course.color}20` }}
                >
                  <Code2 className="w-5 h-5" style={{ color: course.color }} />
                </div>
                <h4 className="font-medium text-foreground group-hover:text-primary transition-colors truncate">
                  {course.name}
                </h4>
              </div>

              {/* Progress bar */}
              <div className="mb-2">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>{t('进度', 'Progress')}</span>
                  <span>{course.progress}%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-primary to-primary-600"
                    style={{ width: `${course.progress}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-end">
                <span className="text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                  {t('继续', 'Continue')}
                  <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
