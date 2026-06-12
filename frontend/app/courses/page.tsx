'use client'

import Link from 'next/link'
import { ArrowLeft, Users, ArrowRight } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { getCourseConfig } from '@/lib/icons/course-icons'
import { cn } from '@/lib/utils'
import { useCoursesData } from './hooks/use-courses-data'

export default function CoursesPage() {
  const { mounted, courses, isLoading } = useCoursesData()

  if (!mounted || isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full size-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            <Link
              href={getStoredToken() ? '/dashboard' : '/'}
              className="flex items-center gap-2 px-2 py-1 rounded-lg text-muted-foreground hover:bg-secondary transition-colors"
            >
              <ArrowLeft className="size-4" strokeWidth={1.5} />
              <span className="text-sm">返回</span>
            </Link>
            <h1 className="text-lg font-semibold text-foreground">选择课程</h1>
            <div className="w-20" />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="pt-24 pb-12 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Title */}
          <div className="text-center mb-12">
            <h2 className="text-3xl font-semibold text-foreground mb-4">
              选择你的学习课程
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              从入门到进阶，覆盖主流编程语言和核心计算机科学知识
            </p>
          </div>

          {/* Course grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {courses.map((course) => {
              const courseConfig = getCourseConfig(course.code)
              return (
                <div key={course.id}>
                  <Link href={`/mastery/${course.id}`} className="block">
                    <Card
                      variant="default"
                      padding="lg"
                      className="h-full relative overflow-hidden rounded-lg border border-border bg-card hover:border-primary transition-colors cursor-pointer"
                    >
                      {/* Accent bar */}
                      <div className="absolute top-0 left-0 right-0 h-1 bg-primary" />

                      {/* Icon + Name */}
                      <div className="flex items-center gap-4 mb-4 mt-2">
                        <div
                          className={cn(
                            'size-14 rounded-lg flex items-center justify-center bg-primary-100',
                            !courseConfig && 'bg-secondary',
                          )}
                        >
                          <div className="size-7 text-primary">
                            {courseConfig?.icon}
                          </div>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-foreground">
                            {course.name}
                          </h3>
                          <div className="flex gap-1 mt-1">
                            {Array.from({ length: 4 }, (_, index) => (
                              <div
                                key={index}
                                className={`size-1.5 rounded-full ${index < course.difficulty ? 'bg-primary' : 'bg-muted'}`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-muted-foreground mb-4 line-clamp-2 leading-relaxed">
                        {course.description}
                      </p>

                      {/* Bottom info */}
                      <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-border">
                        <span className="flex items-center gap-1">
                          <Users className="size-3.5" strokeWidth={1.5} />
                          {course.learners} 学习者
                        </span>
                        <span className="flex items-center gap-1 text-primary font-medium">
                          进入学习
                          <ArrowRight className="size-3" strokeWidth={1.5} />
                        </span>
                      </div>
                    </Card>
                  </Link>
                </div>
              )
            })}
          </div>
        </div>
      </main>
    </div>
  )
}
