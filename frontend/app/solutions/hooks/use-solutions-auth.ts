'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, getStoredUser } from '@/lib/api/auth'
import type { User } from '@/lib/api/auth'

interface SolutionsAuthState {
  currentUser: User | null
  isAdmin: boolean
  lang: 'zh' | 'en'
}

export function useSolutionsAuth(): SolutionsAuthState & { push: ReturnType<typeof useRouter>['push'] } {
  const { push } = useRouter()
  const [state, setState] = useState<SolutionsAuthState>({
    currentUser: null,
    isAdmin: false,
    lang: 'zh',
  })

  useEffect(() => {
    const user = getStoredUser()
    const token = getStoredToken()

    if (!token || !user) {
      push('/login')
      return
    }

    const savedLang = localStorage.getItem('language') || 'zh'
    setState({
      currentUser: user,
      isAdmin: user.is_admin || false,
      lang: savedLang as 'zh' | 'en',
    })
  }, [push])

  return { ...state, push }
}
