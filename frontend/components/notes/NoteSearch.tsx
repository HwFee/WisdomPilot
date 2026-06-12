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
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" strokeWidth={1.5} />
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder || t('搜索笔记...', 'Search notes...')}
        aria-label={placeholder || t('搜索笔记', 'Search notes')}
        className="w-full h-10 pl-10 pr-10 bg-background border border-border text-sm focus:outline-none focus:border-foreground transition-colors"
      />
      {query && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => setQuery('')}
          className="absolute right-1 top-1/2 -translate-y-1/2 size-8"
          aria-label={t('清除搜索', 'Clear search')}
        >
          <X className="size-4 text-muted-foreground" strokeWidth={1.5} />
        </Button>
      )}
      {isSearching && (
        <div className="absolute right-12 top-1/2 -translate-y-1/2">
          <div className="size-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  )
}
