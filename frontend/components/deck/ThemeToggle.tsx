'use client'

import { useEffect, useState } from 'react'

const THEME_STORAGE_KEY = 'deck-theme'

function currentTheme(): 'dark' | 'light' {
  if (typeof document === 'undefined') return 'dark'
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark'
}

/** 色系切换：暗夜控制台（默认）/ 日光仪表台 */
export function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')

  useEffect(() => {
    setTheme(currentTheme())
  }, [])

  const toggle = () => {
    const next = theme === 'light' ? 'dark' : 'light'
    if (next === 'light') {
      document.documentElement.setAttribute('data-theme', 'light')
    } else {
      document.documentElement.removeAttribute('data-theme')
    }
    try {
      localStorage.setItem(THEME_STORAGE_KEY, next)
    } catch {
      /* ignore */
    }
    setTheme(next)
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="切换色系"
      className="font-mono text-[11px] tracking-wider text-dim bg-transparent border border-line rounded px-2.5 py-1 cursor-pointer transition-colors hover:text-signal hover:border-signal"
    >
      {theme.toUpperCase()}
    </button>
  )
}
