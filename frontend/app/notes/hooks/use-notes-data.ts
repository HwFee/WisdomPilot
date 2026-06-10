'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout } from '@/lib/api'
import { getNotes, getNoteTags } from '@/lib/api/notes'
import { filterNotesByTags, filterNotesBySearch } from '../lib/notes-filter'
import type { NoteResponse } from '@/types/api'

export function useNotesData() {
  const { push, back } = useRouter()
  const [notes, setNotes] = useState<NoteResponse[]>([])
  const [filteredNotes, setFilteredNotes] = useState<NoteResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const hasFetched = useRef(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchData = useCallback(async (token: string) => {
    try {
      const [notesData] = await Promise.all([
        getNotes(token),
        getNoteTags(token),
      ])
      setNotes(notesData.notes)
    } catch {
      // Handle error silently
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchDataRef = useRef(fetchData)
  fetchDataRef.current = fetchData

  // Polling: refresh every 3s when there are processing notes
  useEffect(() => {
    const hasProcessing = notes.some(
      (n) => n.processing_status === 'pending' || n.processing_status === 'processing',
    )

    if (hasProcessing) {
      pollingRef.current = setInterval(() => {
        const token = getStoredToken()
        if (token) {
          fetchDataRef.current(token)
        }
      }, 3000)
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [notes])

  // Initial load
  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    if (!token) {
      logout()
      push('/login')
      return
    }
    hasFetched.current = true
    fetchData(token)
  }, [push, back, fetchData])

  // Apply filters when dependencies change
  useEffect(() => {
    let result = notes
    result = filterNotesByTags(result, selectedTags)
    result = filterNotesBySearch(result, searchQuery)
    setFilteredNotes(result)
  }, [notes, selectedTags, searchQuery])

  const handleDelete = useCallback((noteId: string) => {
    setNotes((prev) => prev.filter((n) => n.id !== noteId))
  }, [])

  const handleSave = useCallback((savedNote: NoteResponse) => {
    setNotes((prev) => {
      const existing = prev.find((n) => n.id === savedNote.id)
      if (existing) {
        return prev.map((n) => (n.id === savedNote.id ? savedNote : n))
      }
      return [savedNote, ...prev]
    })
  }, [])

  const handleSearchResults = useCallback(
    (results: NoteResponse[], query: string) => {
      if (query) {
        setSearchQuery(query)
        setFilteredNotes(results)
      } else {
        setSearchQuery('')
        setFilteredNotes(filterNotesByTags(notes, selectedTags))
      }
    },
    [notes, selectedTags],
  )

  return {
    notes,
    filteredNotes,
    isLoading,
    selectedTags,
    setSelectedTags,
    searchQuery,
    handleDelete,
    handleSave,
    handleSearchResults,
    back,
  }
}
