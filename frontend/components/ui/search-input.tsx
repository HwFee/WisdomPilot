'use client'

import { Search, X } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

interface SearchInputProps {
  placeholder?: string
  value: string
  onChange: (value: string) => void
  className?: string
}

export function SearchInput({
  placeholder = '搜索课程',
  value,
  onChange,
  className = ''
}: SearchInputProps) {
  const [isFocused, setIsFocused] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

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
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        inputRef.current?.blur()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div
      className={`
        relative flex items-center gap-2 px-4 py-2 rounded-xl
        bg-gray-100 border transition-all duration-200
        ${isFocused
          ? 'border-blue-400 bg-white shadow-sm ring-2 ring-blue-100'
          : 'border-transparent hover:bg-gray-50'
        }
        ${className}
      `}
    >
      <Search className={`size-4 shrink-0 ${isFocused ? 'text-blue-500' : 'text-gray-400'} transition-colors`} />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder={placeholder}
        className="flex-1 min-w-0 bg-transparent outline-none text-sm text-gray-700 placeholder:text-gray-400"
      />
      {value ? (
        <button type="button"
          onClick={handleClear}
          className="p-0.5 rounded-full hover:bg-gray-200 transition-colors shrink-0"
          aria-label="清除搜索"
        >
          <X className="size-3.5 text-gray-400 hover:text-gray-600" />
        </button>
      ) : isFocused ? (
        <span className="text-xs text-gray-400 shrink-0 bg-gray-200 px-1.5 py-0.5 rounded">Esc</span>
      ) : (
        <span className="text-xs text-gray-400 shrink-0 hidden sm:inline">Ctrl+K</span>
      )}
    </div>
  )
}
