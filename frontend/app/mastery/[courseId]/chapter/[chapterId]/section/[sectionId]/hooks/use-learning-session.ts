'use client'

import { useRef, useEffect, useCallback } from 'react'
import { getStoredToken } from '@/lib/api'
import { startLearningSession, endLearningSessionKeepalive } from '@/lib/api/stats'
import type { SectionDetail } from '@/lib/api/sections'

export function useLearningSession(sectionId: number, section: SectionDetail | null) {
  const sessionStartedAtRef = useRef<number | null>(null)
  const sessionInitializedRef = useRef(false)
  const sessionEndedRef = useRef(false)
  const chapterIdRef = useRef<number | null>(null)

  const startTrackedSession = useCallback(async (chapterId: number) => {
    const token = getStoredToken()
    if (!token || sessionInitializedRef.current) return

    try {
      await startLearningSession(token, chapterId, 0)
      const now = Date.now()
      sessionStartedAtRef.current = now
      sessionInitializedRef.current = true
      sessionEndedRef.current = false
      chapterIdRef.current = chapterId
    } catch {
      // Session start failed - will retry on next interaction
    }
  }, [])

  const endTrackedSession = useCallback(() => {
    if (sessionEndedRef.current) return

    const token = getStoredToken()
    const startedAt = sessionStartedAtRef.current

    if (!token || !startedAt || !sessionInitializedRef.current) return

    const durationSeconds = Math.max(1, Math.floor((Date.now() - startedAt) / 1000))

    sessionEndedRef.current = true
    sessionInitializedRef.current = false
    sessionStartedAtRef.current = null

    endLearningSessionKeepalive(token, durationSeconds, chapterIdRef.current ?? undefined)
  }, [])

  const transferSession = useCallback(() => {
    if (sessionStartedAtRef.current && sessionInitializedRef.current) {
      const sessionData = {
        startedAt: sessionStartedAtRef.current,
        chapterId: chapterIdRef.current,
        fromSection: sectionId,
      }
      try {
        localStorage.setItem('masterySession:v1', JSON.stringify(sessionData))
      } catch (e) {
        console.warn('Failed to save session to localStorage:', e)
      }
      sessionEndedRef.current = true
    }
  }, [sectionId])

  // Start session when section loads
  useEffect(() => {
    if (section && !sessionInitializedRef.current) {
      startTrackedSession(section.chapter_id)
    }
  }, [section, startTrackedSession])

  // Distinguish StrictMode fake unmount from real unmount
  const isMountedRef = useRef(false)

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
      requestAnimationFrame(() => {
        if (!isMountedRef.current) {
          endTrackedSession()
        }
      })
    }
  }, [endTrackedSession])

  return { transferSession }
}
