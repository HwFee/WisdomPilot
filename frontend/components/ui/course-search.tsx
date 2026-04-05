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

  // Search function
  const searchChapters = useCallback((query: string): SearchResult[] => {
    if (!query.trim()) return []

    const lowerQuery = query.toLowerCase().trim()
    const results: SearchResult[] = []

    chapters.forEach((chapter) => {
      // Check chapter title
      if (chapter.title.toLowerCase().includes(lowerQuery)) {
        results.push({
          type: 'chapter',
          chapter,
          matchText: chapter.title,
        })
        return
      }
      if (chapter.titleEn.toLowerCase().includes(lowerQuery)) {
        results.push({
          type: 'chapter',
          chapter,
          matchText: chapter.titleEn,
        })
        return
      }

      // Check subsections
      chapter.subsections.forEach((subsection, idx) => {
        if (subsection.toLowerCase().includes(lowerQuery)) {
          results.push({
            type: 'subsection',
            chapter,
            subsection,
            subsectionIndex: idx,
            matchText: subsection,
          })
        }
      })
    })

    // Limit results
    return results.slice(0, 8)
  }, [chapters])

  // Update search results when value changes
  useEffect(() => {
    if (value.trim()) {
      const searchResults = searchChapters(value)
      setResults(searchResults)
      setShowDropdown(searchResults.length > 0)
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
          bg-white border transition-all duration-200
          ${isFocused
            ? 'border-blue-400 shadow-sm ring-2 ring-blue-100'
            : 'border-gray-200 hover:border-gray-300'
          }
        `}
      >
        <Search className={`w-4 h-4 shrink-0 ${isFocused ? 'text-blue-500' : 'text-gray-400'} transition-colors`} />
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 min-w-0 bg-transparent outline-none text-sm text-gray-700 placeholder:text-gray-400"
        />
        {value ? (
          <button
            onClick={handleClear}
            className="p-0.5 rounded-full hover:bg-gray-100 transition-colors shrink-0"
            aria-label="清除搜索"
          >
            <X className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
          </button>
        ) : isFocused ? (
          <span className="text-xs text-gray-400 shrink-0 bg-gray-100 px-1.5 py-0.5 rounded">Esc</span>
        ) : (
          <span className="text-xs text-gray-400 shrink-0 hidden sm:inline">Ctrl+K</span>
        )}
      </div>

      {/* Dropdown Results */}
      {showDropdown && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden z-50"
        >
          <div className="max-h-80 overflow-y-auto">
            {results.map((result, index) => (
              <button
                key={`${result.chapter.id}-${result.type}-${result.subsection || 'chapter'}`}
                onClick={() => handleSelect(result)}
                className={`
                  w-full flex items-center gap-3 px-4 py-3 text-left transition-colors
                  ${index === selectedIndex ? 'bg-blue-50' : 'hover:bg-gray-50'}
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
                    <span className="font-medium text-gray-900 text-sm">
                      {result.chapter.title}
                    </span>
                    {result.type === 'chapter' && (
                      <span className="text-xs text-gray-400">{result.chapter.titleEn}</span>
                    )}
                  </div>
                  {result.type === 'subsection' && result.subsection && (
                    <p className="text-xs text-gray-500 mt-0.5">
                      {result.subsection}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Footer hint */}
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
            <p className="text-xs text-gray-400">
              按 <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">Enter</kbd> 选择{' '}
              <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs ml-1">↑↓</kbd> 导航{' '}
              <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs ml-1">Esc</kbd> 关闭
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
