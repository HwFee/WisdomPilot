'use client'

import { useState, useEffect } from 'react'
import { getStoredToken } from '@/lib/api'
import { getCourses } from '@/lib/api/courses'
import type { CourseSummary } from '@/types/api'

interface CourseDisplay {
  id: number
  code: string
  name: string
  difficulty: number
  description: string
  learners: string
}

const FALLBACK_COURSES: CourseDisplay[] = [
  {
    id: 1,
    code: 'c',
    name: 'C语言程序设计',
    difficulty: 1,
    description: '编程入门首选，打好扎实基础',
    learners: '12,580+',
  },
  {
    id: 2,
    code: 'cpp',
    name: 'C++程序设计',
    difficulty: 2,
    description: '面向对象编程，系统开发利器',
    learners: '8,420+',
  },
  {
    id: 3,
    code: 'python',
    name: 'Python程序设计',
    difficulty: 1,
    description: '简洁优雅，人工智能首选语言',
    learners: '25,800+',
  },
]

function transformCourse(course: CourseSummary): CourseDisplay {
  return {
    id: course.id,
    code: course.code.toLowerCase(),
    name: course.name,
    difficulty: course.difficulty_level || 1,
    description: course.description || `${course.name}课程`,
    learners: '1,000+',
  }
}

export function useCoursesData() {
  const [mounted, setMounted] = useState(false)
  const [courses, setCourses] = useState<CourseDisplay[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = getStoredToken()

    const fetchCourses = async () => {
      try {
        const response = await getCourses(token || undefined)
        if (response.courses && response.courses.length > 0) {
          setCourses(response.courses.map(transformCourse))
        } else {
          setCourses(FALLBACK_COURSES)
        }
      } catch (err) {
        console.error('Failed to fetch courses:', err)
        setCourses(FALLBACK_COURSES)
      } finally {
        setMounted(true)
        setIsLoading(false)
      }
    }

    fetchCourses()
  }, [])

  return { mounted, courses, isLoading }
}
