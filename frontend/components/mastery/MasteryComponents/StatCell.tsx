'use client'

import { LazyMotion, domAnimation, m } from 'framer-motion'
import { MasteryProgressBar, getMasteryLevel } from './ProgressBar'

// ========================================
// SectionMasteryCard - section-level mastery card (the "stat cell" for a section)
// ========================================

interface SectionMasteryCardProps {
  sectionId: number
  title: string
  masteryScore: number
  knowledgePointsCount: number
  masteredPointsCount: number
  isCompleted: boolean
  onClick?: () => void
}

export function SectionMasteryCard({
  title,
  masteryScore,
  knowledgePointsCount,
  masteredPointsCount,
  isCompleted,
  onClick,
}: SectionMasteryCardProps) {
  return (
    <LazyMotion features={domAnimation}>
      <m.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onClick}
        className={`bg-white rounded-xl border p-4 cursor-pointer transition-all ${
          isCompleted ? 'border-green-200 bg-green-50/30' : 'border-gray-100 hover:border-blue-200'
        }`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-gray-900 truncate">{title}</h3>
            <p className="text-sm text-gray-500 mt-1">
              已掌握 {masteredPointsCount}/{knowledgePointsCount} 个知识点
            </p>
          </div>
          <div className="flex-shrink-0 ml-2">
            {isCompleted ? (
              <div className="size-8 rounded-full bg-green-100 flex items-center justify-center">
                <svg className="size-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            ) : (
              <div className="size-8 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-xs font-medium text-blue-600">{masteryScore.toFixed(0)}%</span>
              </div>
            )}
          </div>
        </div>
        <div className="mt-3">
          <MasteryProgressBar score={masteryScore} size="sm" showLabel={false} />
        </div>
      </m.div>
    </LazyMotion>
  )
}

// ========================================
// ChapterMasteryCard - chapter-level mastery card
// ========================================

interface ChapterMasteryCardProps {
  chapterId: number
  title: string
  masteryScore: number
  sectionsCount: number
  completedSectionsCount: number
  isCompleted: boolean
  onClick?: () => void
}

export function ChapterMasteryCard({
  title,
  masteryScore,
  sectionsCount,
  completedSectionsCount,
  isCompleted,
  onClick,
}: ChapterMasteryCardProps) {
  const { badgeColor, textColor, label } = getMasteryLevel(masteryScore)

  return (
    <LazyMotion features={domAnimation}>
      <m.div
        whileHover={{ scale: 1.01 }}
        onClick={onClick}
        className={`bg-white dark:bg-gray-800 rounded-xl border p-5 cursor-pointer transition-all ${
          isCompleted ? 'border-green-200 dark:border-green-800' : 'border-gray-100 dark:border-gray-700 hover:border-blue-200'
        }`}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${badgeColor} ${textColor}`}>
            {label}
          </span>
        </div>

        <MasteryProgressBar score={masteryScore} size="md" />

        <div className="flex items-center justify-between mt-3 text-sm text-gray-500 dark:text-gray-400">
          <span>
            {isCompleted ? (
              <span className="text-green-600 dark:text-green-400 font-medium">✓ 章节已完成</span>
            ) : (
              <span>完成 {completedSectionsCount}/{sectionsCount} 个小节</span>
            )}
          </span>
          <span className="font-medium text-gray-700 dark:text-gray-300">{masteryScore.toFixed(0)}%</span>
        </div>
      </m.div>
    </LazyMotion>
  )
}

// ========================================
// CourseMasteryOverview - top-level course mastery overview with chapters grid
// ========================================

interface CourseMasteryOverviewProps {
  courseName: string
  masteryScore: number
  progressPercentage: number
  chaptersCount: number
  completedChaptersCount: number
  chapters: Array<{
    chapter_id: number
    mastery_score: number
    is_completed: boolean
  }>
  onChapterClick?: (chapterId: number) => void
}

export function CourseMasteryOverview({
  courseName,
  masteryScore,
  progressPercentage,
  chaptersCount,
  completedChaptersCount,
  chapters,
  onChapterClick,
}: CourseMasteryOverviewProps) {
  const { label, textColor } = getMasteryLevel(masteryScore)

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{courseName}</h2>
          <p className="text-sm text-gray-600 mt-1">整体学习进度</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-blue-600">{masteryScore.toFixed(0)}%</div>
          <div className={`text-sm font-medium ${textColor}`}>{label}</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>章节进度</span>
          <span>{completedChaptersCount}/{chaptersCount} 已完成</span>
        </div>
        <MasteryProgressBar score={progressPercentage} size="lg" />
      </div>

      {/* Chapters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {chapters.map((chapter, index) => {
          const { badgeColor, textColor: chapterTextColor } = getMasteryLevel(chapter.mastery_score)
          return (
            <LazyMotion key={chapter.chapter_id} features={domAnimation}>
              <m.div
                whileHover={{ scale: 1.02 }}
                onClick={() => onChapterClick?.(chapter.chapter_id)}
                className={`bg-white dark:bg-gray-800 rounded-lg p-3 cursor-pointer border ${
                  chapter.is_completed ? 'border-green-200 dark:border-green-800' : 'border-gray-100 dark:border-gray-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">章节 {index + 1}</span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${badgeColor} ${chapterTextColor}`}>
                    {chapter.mastery_score.toFixed(0)}%
                  </span>
                </div>
                <div className="mt-2">
                  <MasteryProgressBar score={chapter.mastery_score} size="sm" showLabel={false} />
                </div>
              </m.div>
            </LazyMotion>
          )
        })}
      </div>
    </div>
  )
}
