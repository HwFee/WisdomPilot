'use client'

import { useState, useEffect } from 'react'
import { getCourses } from '@/lib/api/courses'
import type { CourseSummary } from '@/types/api'

interface HomePageState {
  isLoggedIn: boolean
  mounted: boolean
  courses: CourseSummary[]
  coursesLoading: boolean
}

export function useHomeData(): HomePageState {
  const [state, setState] = useState<HomePageState>({
    isLoggedIn: false,
    mounted: false,
    courses: [],
    coursesLoading: true,
  })

  useEffect(() => {
    const token = localStorage.getItem('token:v1')
    const isLoggedInValue = !!token

    getCourses()
      .then((data) => {
        setState({
          isLoggedIn: isLoggedInValue,
          mounted: true,
          courses: data.courses,
          coursesLoading: false,
        })
      })
      .catch((err) => {
        console.error('Failed to fetch courses:', err)
        setState({
          isLoggedIn: isLoggedInValue,
          mounted: true,
          courses: [],
          coursesLoading: false,
        })
      })
  }, [])

  return state
}
