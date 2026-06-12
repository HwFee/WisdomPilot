'use client'

import { useState, useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
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

  const onResultsRef = useRef(onResults)
  useEffect(() => { onResultsRef.current = onResults }, [onResults])

  // Debounced search (latest-ref pattern, inlined to avoid prefer-use-effect-event)
  useEffect(() => {
    if (!query.trim()) {
      onResultsRef.current?.([], '')
      return
    }
    const token = getStoredToken()
    if (!token) return
    setIsSearching(true)
    const timer = setTimeout(async () => {
      try {
        const data: NoteSearchResponse = await searchNotes(token, query.trim())
        onResultsRef.current?.(data.notes, data.query)
      } catch (error) {
        console.error('[搜索] 失败:', error)
      } finally {
        setIsSearching(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  return (
    <div className="relative">
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-5 text-muted-foreground" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder || t('搜索笔记...', 'Search notes...')}
        aria-label={placeholder || t('搜索笔记', 'Search notes')}
        className="w-full pl-11 pr-11 py-3 text-base border-2 rounded-xl bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
      />
      {query && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => setQuery('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 size-8"
          aria-label={t('清除搜索', 'Clear search')}
        >
          <X className="size-5 text-muted-foreground" />
        </Button>
      )}
      {isSearching && (
        <div className="absolute right-12 top-1/2 -translate-y-1/2">
          <div className="size-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  )
}
