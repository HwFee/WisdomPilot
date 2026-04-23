'use client'

import { useState, useCallback, useEffect } from 'react'
import { Search, X } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { searchNotes } from '@/lib/api/notes'
import type { NoteResponse, NoteSearchResponse } from '@/types/api'

interface NoteSearchProps {
  onResults?: (notes: NoteResponse[], query: string) => void
  placeholder?: string
  lang?: 'zh' | 'en'
}

export function NoteSearch({
  onResults,
  placeholder,
  lang = 'zh',
}: NoteSearchProps) {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      onResults?.([], '')
      return
    }

    const token = getStoredToken()
    if (!token) return

    setIsSearching(true)
    try {
      const data: NoteSearchResponse = await searchNotes(token, searchQuery.trim())
      onResults?.(data.notes, data.query)
    } catch (error) {
      console.error('[搜索] 失败:', error)
    } finally {
      setIsSearching(false)
    }
  }, [onResults])

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      handleSearch(query)
    }, 300)

    return () => clearTimeout(timer)
  }, [query, handleSearch])

  return (
    <div className="relative">
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder || t('搜索笔记...', 'Search notes...')}
        className="w-full pl-11 pr-11 py-3 text-base border-2 rounded-xl bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
      />
      {query && (
        <button type="button"
          onClick={() => setQuery('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-muted rounded-lg"
        >
          <X className="w-5 h-5 text-muted-foreground" />
        </button>
      )}
      {isSearching && (
        <div className="absolute right-12 top-1/2 -translate-y-1/2">
          <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  )
}
