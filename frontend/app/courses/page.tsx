'use client'

import Link from 'next/link'
import { LazyMotion, domAnimation, m } from 'framer-motion'
import { ArrowLeft, Users, ArrowRight } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { DifficultyBadge } from '@/components/ui/badge'
import { staggerContainer, staggerItem } from '@/lib/animations'
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
    <LazyMotion features={domAnimation}>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <m.header
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50"
        >
          <div className="max-w-6xl mx-auto px-6">
            <div className="flex items-center justify-between h-16">
              <Link
                href={getStoredToken() ? '/dashboard' : '/'}
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors group"
              >
                <ArrowLeft className="size-4 group-hover:-translate-x-0.5 transition-transform" />
                <span className="text-sm">返回</span>
              </Link>
              <h1 className="text-lg font-semibold text-foreground">选择课程</h1>
              <div className="w-20" />
            </div>
          </div>
        </m.header>

        {/* Main content */}
        <main className="pt-24 pb-12 px-6">
          <div className="max-w-6xl mx-auto">
            {/* Title */}
            <m.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl font-semibold text-foreground mb-4">
                选择你的学习课程
              </h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                从入门到进阶，覆盖主流编程语言和核心计算机科学知识
              </p>
            </m.div>

            {/* Course grid */}
            <m.div
              variants={staggerContainer}
              initial="initial"
              animate="animate"
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto"
            >
              {courses.map((course, index) => {
                const courseConfig = getCourseConfig(course.code)
                return (
                  <m.div
                    key={course.id}
                    variants={staggerItem}
                    custom={index}
                  >
                    <Link href={`/mastery/${course.id}`} className="group block">
                      <Card
                        variant="interactive"
                        padding="lg"
                        className="h-full relative overflow-hidden"
                      >
                        {/* Gradient bar */}
                        <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${courseConfig?.gradient || 'from-primary to-primary-600'}`} />

                        {/* Icon + Name */}
                        <div className="flex items-center gap-4 mb-4 mt-2">
                          <m.div
                            whileHover={{ scale: 1.08 }}
                            className={cn(
                              'size-14 rounded-xl flex items-center justify-center shadow-lg',
                              courseConfig
                                ? `bg-gradient-to-br ${courseConfig.gradient}`
                                : 'bg-gradient-to-br from-primary to-primary-600',
                            )}
                          >
                            <div className="size-7 text-white">
                              {courseConfig?.icon}
                            </div>
                          </m.div>
                          <div>
                            <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                              {course.name}
                            </h3>
                            <div className="flex gap-1 mt-1">
                              {Array.from({ length: 4 }, (_, i) => (
                                <div
                                  key={i}
                                  className={`size-1.5 rounded-full ${i < course.difficulty ? 'bg-primary' : 'bg-muted'}`}
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
                        <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-border/50">
                          <span className="flex items-center gap-1">
                            <Users className="size-3.5" />
                            {course.learners} 学习者
                          </span>
                          <span className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                            进入学习
                            <ArrowRight className="size-3" />
                          </span>
                        </div>
                      </Card>
                    </Link>
                  </m.div>
                )
              })}
            </m.div>
          </div>
        </main>
      </div>
    </LazyMotion>
  )
}
