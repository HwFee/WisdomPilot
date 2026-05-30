'use client'

import { Code2, Target, BookOpen, ChevronDown } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import type { CourseProgress } from '@/lib/api/courses'

interface CourseSwitcherProps {
  courses: CourseProgress[]
  currentCourseId: number | null
  onSwitch: (courseId: number) => void
  lang?: 'zh' | 'en'
}

const COURSE_GRADIENTS: Record<string, string> = {
  'C': 'from-blue-500 to-cyan-500',
  'CPP': 'from-indigo-500 to-purple-500',
  'Python': 'from-green-500 to-teal-500',
}

export function CourseSwitcher({
  courses,
  currentCourseId,
  onSwitch,
  lang = 'zh'
}: CourseSwitcherProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const currentCourse = courses.find(c => c.course_id === currentCourseId) || courses[0]

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (courseId: number) => {
    onSwitch(courseId)
    setIsOpen(false)
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">{t('正在学习', 'Learning')}:</span>
      <div className="relative" ref={dropdownRef}>
        <button type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 border border-border rounded-lg hover:bg-muted transition-colors"
        >
          {currentCourse && (
            <>
              <div className={`size-5 rounded bg-gradient-to-br ${COURSE_GRADIENTS[currentCourse.course_code] || 'from-gray-500 to-gray-600'} flex items-center justify-center`}>
                <span className="text-white text-xs font-bold">
                  {currentCourse.course_code.charAt(0)}
                </span>
              </div>
              <span className="text-sm truncate max-w-[120px]">{currentCourse.course_name}</span>
              {currentCourse.progress > 0 && (
                <span className="text-xs text-muted-foreground">
                  {currentCourse.progress}%
                </span>
              )}
              <ChevronDown className={`size-4 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </>
          )}
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 mt-1 w-[240px] bg-card border border-border rounded-lg shadow-lg z-50 max-h-[300px] overflow-auto">
            {courses.map((course) => {
              const hasProgress = course.progress > 0
              const isSelected = course.course_id === currentCourseId

              return (
                <button type="button"
                  key={course.course_id}
                  onClick={() => handleSelect(course.course_id)}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-muted transition-colors ${
                    isSelected ? 'bg-primary/10' : ''
                  }`}
                >
                  <div className={`size-5 rounded bg-gradient-to-br ${COURSE_GRADIENTS[course.course_code] || 'from-gray-500 to-gray-600'} flex items-center justify-center`}>
                    <span className="text-white text-xs font-bold">
                      {course.course_code.charAt(0)}
                    </span>
                  </div>
                  <span className="flex-1 text-sm truncate">{course.course_name}</span>
                  {hasProgress ? (
                    <span className="text-xs text-muted-foreground">
                      {course.progress}%
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">
                      {t('未开始', 'New')}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
