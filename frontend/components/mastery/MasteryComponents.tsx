/**
 * BKT Mastery Components
 *
 * 掌握度显示组件，支持四层聚合：
 * - 知识点掌握度
 * - 小节掌握度
 * - 章节掌握度
 * - 课程掌握度
 */

'use client'

import { LazyMotion, domAnimation, m } from 'framer-motion'

// ========== 掌握度进度条 ==========

interface MasteryProgressBarProps {
  /** 掌握度 0-100 */
  score: number
  /** 是否显示百分比标签 */
  showLabel?: boolean
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否显示动画 */
  animated?: boolean
}

const HEIGHT_MAP = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
}

export function MasteryProgressBar({
  score,
  showLabel = true,
  size = 'md',
  animated = true,
}: MasteryProgressBarProps) {
  const normalizedScore = Math.min(100, Math.max(0, score))
  const { textColor, label, progressColor } = getMasteryLevel(normalizedScore)

  return (
    <LazyMotion features={domAnimation}>
      <div className="w-full">
        <div className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full ${HEIGHT_MAP[size]} overflow-hidden`}>
          <m.div
            className={`${HEIGHT_MAP[size]} rounded-full ${progressColor}`}
            initial={animated ? { width: 0 } : { width: `${normalizedScore}%` }}
            animate={{ width: `${normalizedScore}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      {showLabel && (
        <div className="flex justify-between items-center mt-1">
          <span className={`text-xs font-medium ${textColor}`}>{label}</span>
          <span className="text-xs text-gray-500">{normalizedScore.toFixed(0)}%</span>
        </div>
      )}
      </div>
    </LazyMotion>
  )
}

// ========== 知识点掌握度卡片 ==========

interface KnowledgePointMasteryProps {
  name: string
  pL: number // 0-1 的掌握概率
  totalAttempts: number
  correctAttempts: number
  isMastered: boolean
}

function KnowledgePointMasteryCard({
  name,
  pL,
  totalAttempts,
  correctAttempts,
  isMastered,
}: KnowledgePointMasteryProps) {
  const score = pL * 100
  const accuracy = totalAttempts > 0 ? (correctAttempts / totalAttempts) * 100 : 0

  return (
    <div className="bg-white rounded-lg border border-gray-100 p-3 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-gray-900 truncate">{name}</h4>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            <span>尝试 {totalAttempts} 次</span>
            <span>•</span>
            <span>正确率 {accuracy.toFixed(0)}%</span>
          </div>
        </div>
        <div className="flex-shrink-0 ml-2">
          {isMastered ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
              ✓ 已掌握
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
              学习中
            </span>
          )}
        </div>
      </div>
      <div className="mt-2">
        <MasteryProgressBar score={score} size="sm" showLabel={false} />
      </div>
    </div>
  )
}

// ========== 小节掌握度卡片 ==========

interface SectionMasteryCardProps {
  sectionId: number
  title: string
  masteryScore: number
  knowledgePointsCount: number
  masteredPointsCount: number
  isCompleted: boolean
  onClick?: () => void
}

function SectionMasteryCard({
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

// ========== 章节掌握度卡片 ==========

interface ChapterMasteryCardProps {
  chapterId: number
  title: string
  masteryScore: number
  sectionsCount: number
  completedSectionsCount: number
  isCompleted: boolean
  onClick?: () => void
}

function ChapterMasteryCard({
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

// ========== 课程掌握度概览 ==========

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

function CourseMasteryOverview({
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

// ========== 辅助函数 ==========

function getMasteryLevel(score: number) {
  if (score >= 95) {
    return {
      label: '精通',
      badgeColor: 'bg-green-100 dark:bg-green-900/30',
      textColor: 'text-green-700 dark:text-green-400',
      progressColor: 'bg-gradient-to-r from-green-500 to-emerald-400',
    }
  } else if (score >= 85) {
    return {
      label: '熟练',
      badgeColor: 'bg-blue-100 dark:bg-blue-900/30',
      textColor: 'text-blue-700 dark:text-blue-400',
      progressColor: 'bg-gradient-to-r from-blue-500 to-cyan-400',
    }
  } else if (score >= 70) {
    return {
      label: '练习',
      badgeColor: 'bg-yellow-100 dark:bg-yellow-900/30',
      textColor: 'text-yellow-700 dark:text-yellow-400',
      progressColor: 'bg-gradient-to-r from-yellow-500 to-amber-400',
    }
  } else if (score >= 50) {
    return {
      label: '学习',
      badgeColor: 'bg-orange-100 dark:bg-orange-900/30',
      textColor: 'text-orange-700 dark:text-orange-400',
      progressColor: 'bg-gradient-to-r from-orange-500 to-amber-400',
    }
  } else {
    return {
      label: '入门',
      badgeColor: 'bg-gray-100 dark:bg-gray-800',
      textColor: 'text-gray-600 dark:text-gray-400',
      progressColor: 'bg-gradient-to-r from-gray-400 to-gray-300',
    }
  }
}
