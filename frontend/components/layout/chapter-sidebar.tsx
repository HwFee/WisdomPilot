'use client'

import { useEffect } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { ChevronRight } from 'lucide-react'
import { CourseChapter } from '@/lib/course-data'

interface ChapterSidebarProps {
  chapter: CourseChapter
  isOpen: boolean
  activeIndex: number
  onSelectSubsection: (index: number) => void
  lang: 'zh' | 'en'
}

const SIDEBAR_EXPANDED = 283
const SIDEBAR_COLLAPSED = 51
const SIDEBAR_TRANSITION = {
  duration: 0.3,
  ease: [0.22, 1, 0.36, 1] as const,
}

export function ChapterSidebar({
  chapter,
  isOpen,
  activeIndex,
  onSelectSubsection,
  lang,
}: ChapterSidebarProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const prefersReducedMotion = useReducedMotion()

  const transition = prefersReducedMotion
    ? { duration: 0.05 }
    : SIDEBAR_TRANSITION

  const width = isOpen ? SIDEBAR_EXPANDED : SIDEBAR_COLLAPSED

  return (
    <motion.aside
      animate={{ width }}
      transition={transition}
      className="fixed top-14 left-0 bottom-0 z-40 bg-card border-r border-border overflow-hidden"
    >
      <nav className="h-full flex flex-col">
        {/* Subsections scrollable area */}
        <div className="flex-1 overflow-y-auto py-2">
          {chapter.subsections.map((subsection, index) => {
            const isActive = index === activeIndex
            return (
              <motion.button
                key={subsection}
                onClick={() => onSelectSubsection(index)}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-sm relative
                  ${isActive ? 'text-primary font-medium' : 'text-muted-foreground hover:text-foreground'}
                `}
                whileHover={prefersReducedMotion ? {} : { x: 2 }}
                transition={{ duration: 0.15 }}
              >
                {/* Active indicator bar */}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-full"
                    style={{ backgroundColor: chapter.color }}
                    transition={SIDEBAR_TRANSITION}
                  />
                )}

                {/* Number badge */}
                <span
                  className={`
                    w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 font-medium
                    transition-colors duration-200
                    ${isActive ? 'text-white' : 'bg-muted text-muted-foreground'}
                  `}
                  style={isActive ? { backgroundColor: chapter.color } : {}}
                >
                  {index + 1}
                </span>

                {/* Subsection text - animated */}
                <AnimatePresence>
                  {isOpen && (
                    <motion.span
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -8 }}
                      transition={transition}
                      className="truncate flex-1"
                    >
                      {subsection}
                    </motion.span>
                  )}
                </AnimatePresence>

                {/* Active arrow */}
                <AnimatePresence>
                  {isActive && isOpen && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.5 }}
                      transition={transition}
                    >
                      <ChevronRight className="w-4 h-4 shrink-0" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.button>
            )
          })}
        </div>
      </nav>
    </motion.aside>
  )
}
