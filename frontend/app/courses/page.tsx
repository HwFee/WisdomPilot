'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { PageContainer, SectionHeader } from '@/components/layout'
import { CourseCard } from '../components/course-card'
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
        <div className="max-w-[1280px] mx-auto px-6 lg:px-12">
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
      <main className="pt-24 pb-12">
        <PageContainer>
          <SectionHeader title="全部课程" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <CourseCard
                key={course.id}
                course={{
                  id: course.id,
                  code: course.code,
                  name: course.name,
                  description: course.description,
                  difficulty_level: course.difficulty,
                  learners: course.learners,
                }}
              />
            ))}
          </div>
        </PageContainer>
      </main>
    </div>
  )
}
