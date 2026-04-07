'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Search, X } from 'lucide-react'
import { CourseChapter } from '@/lib/course-data'

interface CourseSearchProps {
  chapters: CourseChapter[]
  value: string
  onChange: (value: string) => void
  onSelect?: (chapter: CourseChapter, subsectionIndex?: number) => void
  placeholder?: string
  className?: string
}

interface SearchResult {
  type: 'chapter' | 'subsection'
  chapter: CourseChapter
  subsection?: string
  subsectionIndex?: number
  matchText: string
}

export function CourseSearch({
  chapters,
  value,
  onChange,
  onSelect,
  placeholder = '搜索课程、小节...',
  className = ''
}: CourseSearchProps) {
  const [isFocused, setIsFocused] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Chinese fuzzy match - splits query into chars and matches if all chars appear
  const chineseMatch = (text: string, query: string): boolean => {
    const chars = query.split('').filter(c => c.trim() && !'和与的了是都'.includes(c))
    if (chars.length === 0) return false
    return chars.every(char => text.includes(char))
  }

  // Score a match (higher = better)
  const scoreMatch = (chapter: CourseChapter, query: string, isChapterTitle: boolean, matchText?: string): number => {
    const q = query.toLowerCase().trim()
    let score = 0
    if (isChapterTitle) {
      if (chapter.title.toLowerCase().includes(q)) score = 100
      else if (chineseMatch(chapter.title, query)) score = 80
      else if (chapter.titleEn.toLowerCase().includes(q)) score = 60
    } else {
      const text = matchText || ''
      if (text.toLowerCase().includes(q)) score = 40
      else if (chineseMatch(text, query)) score = 30
    }
    return score
  }

  // Search function - fuzzy Chinese match + relevance scoring
  const searchChapters = useCallback((query: string): SearchResult[] => {
    if (!query.trim()) return []

    const lowerQuery = query.toLowerCase().trim()
    const scoredResults: { result: SearchResult; score: number }[] = []

    chapters.forEach((chapter) => {
      // Check chapter title
      let chapterScore = scoreMatch(chapter, query, true)
      if (chapterScore > 0) {
        scoredResults.push({
          result: {
            type: 'chapter',
            chapter,
            matchText: chapter.title,
          },
          score: chapterScore,
        })
      }

      // Check subsections
      chapter.subsections.forEach((subsection, idx) => {
        const subScore = scoreMatch(chapter, query, false, subsection)
        if (subScore > 0) {
          scoredResults.push({
            result: {
              type: 'subsection',
              chapter,
              subsection,
              subsectionIndex: idx,
              matchText: subsection,
            },
            score: subScore,
          })
        }
      })
    })

    // Sort by score descending, limit to 8
    return scoredResults
      .sort((a, b) => b.score - a.score)
      .slice(0, 8)
      .map(({ result }) => result)
  }, [chapters])

  // Update search results when value changes
  useEffect(() => {
    if (value.trim()) {
      const searchResults = searchChapters(value)
      setResults(searchResults)
      setShowDropdown(true)  // 始终显示下拉框，有结果则列结果，无结果则显示提示
      setSelectedIndex(-1)
    } else {
      setResults([])
      setShowDropdown(false)
      setSelectedIndex(-1)
    }
  }, [value, searchChapters])

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1))
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleSelect(results[selectedIndex])
        }
        break
      case 'Escape':
        setShowDropdown(false)
        inputRef.current?.blur()
        break
    }
  }

  const handleSelect = (result: SearchResult) => {
    onSelect?.(result.chapter, result.subsectionIndex)
    setShowDropdown(false)
    onChange('')
  }

  const handleClear = () => {
    onChange('')
    inputRef.current?.focus()
  }

  // Handle keyboard shortcut (Ctrl/Cmd + K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className={`relative ${className}`}>
      {/* Search Input */}
      <div
        className={`
          relative flex items-center gap-2 px-4 py-2.5 rounded-xl
          bg-card border transition-all duration-200
          ${isFocused
            ? 'border-blue-400 shadow-sm ring-2 ring-blue-100'
            : 'border-border hover:border-muted-foreground'
          }
        `}
      >
        <Search className={`w-4 h-4 shrink-0 ${isFocused ? 'text-blue-500' : 'text-muted-foreground'} transition-colors`} />
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => {
            setIsFocused(true)
            // 聚焦时如果有搜索词和结果，显示下拉框
            if (value.trim()) {
              setShowDropdown(true)
            }
          }}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 min-w-0 bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground"
        />
        {value ? (
          <button
            onClick={handleClear}
            className="p-0.5 rounded-full hover:bg-muted transition-colors shrink-0"
            aria-label="清除搜索"
          >
            <X className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
          </button>
        ) : isFocused ? (
          <span className="text-xs text-muted-foreground shrink-0 bg-muted px-1.5 py-0.5 rounded">Esc</span>
        ) : (
          <span className="text-xs text-muted-foreground shrink-0 hidden sm:inline">Ctrl+K</span>
        )}
      </div>

      {/* Dropdown Results */}
      {showDropdown && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-2 bg-card rounded-xl border border-border shadow-lg overflow-hidden z-50"
        >
          <div className="max-h-80 overflow-y-auto">
            {results.length === 0 ? (
              /* 无结果提示 */
              <div className="flex flex-col items-center justify-center py-8 px-4 text-muted-foreground">
                <Search className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm font-medium">未找到相关课程</p>
                <p className="text-xs mt-1">尝试其他关键词</p>
              </div>
            ) : (
              results.map((result, index) => (
                <button
                  key={`${result.chapter.id}-${result.type}-${result.subsection || 'chapter'}`}
                  onClick={() => handleSelect(result)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 text-left transition-colors
                    ${index === selectedIndex ? 'bg-primary/5' : 'hover:bg-muted'}
                  `}
                >
                  {/* Number badge */}
                  <span
                    className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
                    style={{
                      backgroundColor: `${result.chapter.color}15`,
                      color: result.chapter.color,
                    }}
                  >
                    {result.type === 'chapter' ? result.chapter.num : `${result.chapter.num}-${(result.subsectionIndex || 0) + 1}`}
                  </span>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-foreground text-sm">
                        {result.chapter.title}
                      </span>
                      {result.type === 'chapter' && (
                        <span className="text-xs text-muted-foreground">{result.chapter.titleEn}</span>
                      )}
                    </div>
                    {result.type === 'subsection' && result.subsection && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {result.subsection}
                      </p>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Footer hint */}
          <div className="px-4 py-2 bg-muted/50 border-t border-border">
            <p className="text-xs text-muted-foreground">
              按 <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Enter</kbd> 选择{' '}
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs ml-1">↑↓</kbd> 导航{' '}
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs ml-1">Esc</kbd> 关闭
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
