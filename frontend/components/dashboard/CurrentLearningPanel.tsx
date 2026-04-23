'use client'

import { useState, useEffect } from 'react'
import { Trophy, Swords, ChevronRight, CheckCircle, XCircle, Loader2, Star } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { CourseSwitcher } from './CourseSwitcher'
import { useRouter } from 'next/navigation'
import { getMasteryOverview, type MasteryOverviewResponse } from '@/lib/api/learning-path'
import { getStoredToken } from '@/lib/api'
import type { CourseProgress } from '@/lib/api/courses'
import { getTierConfig } from '@/lib/icons/tier-icons'
import { staggerContainer, staggerItem, scaleIn } from '@/lib/animations'

interface RecentExercise {
  stageName: string
  isCorrect: boolean
  time?: string
}

interface CurrentLearningPanelProps {
  courses: CourseProgress[]
  currentCourseId: number | null
  onSwitchCourse: (courseId: number) => void
  recentExercises?: RecentExercise[]
  lang?: 'zh' | 'en'
}

const TIER_NAMES: Record<string, string> = {
  bronze: '青铜',
  silver: '白银',
  gold: '黄金',
  platinum: '铂金',
  diamond: '钻石',
  master: '星耀',
  king: '王者',
}

// 不再使用emoji，改用 tier-icons 中的 SVG 组件
// TIER_ICONS 已被 getTierConfig() 替代

const TIER_COLORS: Record<string, string> = {
  bronze: '#CD7F32',
  silver: '#C0C0C0',
  gold: '#FFD700',
  platinum: '#E5E4E2',
  diamond: '#B9F2FF',
  master: '#9370DB',
  king: '#FF4500',
}

const SUB_TIER_LABELS: Record<number, string> = {
  1: 'I',
  2: 'II',
  3: 'III',
  4: 'IV',
  5: 'V',
}

function getTierFullName(tier: string, subTier: number | null): string {
  const tierName = TIER_NAMES[tier] || tier
  if (subTier && SUB_TIER_LABELS[subTier]) {
    return `${tierName}${SUB_TIER_LABELS[subTier]}`
  }
  return tierName
}

const MASTERY_LEVELS = [
  { min: 0, max: 30, name: '入门', color: 'text-gray-500' },
  { min: 31, max: 50, name: '学习', color: 'text-blue-500' },
  { min: 51, max: 70, name: '练习', color: 'text-green-500' },
  { min: 71, max: 85, name: '熟练', color: 'text-yellow-500' },
  { min: 86, max: 100, name: '精通', color: 'text-purple-500' },
]

function getMasteryLevel(score: number | null) {
  if (score === null) return MASTERY_LEVELS[0]
  return MASTERY_LEVELS.find(l => score >= l.min && score <= l.max) || MASTERY_LEVELS[0]
}

export function CurrentLearningPanel({
  courses,
  currentCourseId,
  onSwitchCourse,
  recentExercises = [],
  lang = 'zh'
}: CurrentLearningPanelProps) {
  const router = useRouter()
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const [isNavigating, setIsNavigating] = useState<'mastery' | 'challenge' | null>(null)
  const [selectedDifficulty, setSelectedDifficulty] = useState<number | null>(null)
  const [showDifficultyModal, setShowDifficultyModal] = useState(false)
  const [masteryOverview, setMasteryOverview] = useState<MasteryOverviewResponse | null>(null)

  // Fetch mastery overview when course changes
  useEffect(() => {
    if (!currentCourseId) return
    const token = getStoredToken()
    if (!token) return

    getMasteryOverview(currentCourseId, token)
      .then(data => setMasteryOverview(data))
      .catch(() => setMasteryOverview(null))
  }, [currentCourseId])

  const currentCourse = courses.find(c => c.course_id === currentCourseId) || courses[0]

  if (!currentCourse) {
    return (
      <div className="bg-card rounded-2xl border border-border p-6 h-full flex items-center justify-center">
        <p className="text-muted-foreground">{t('暂无课程数据', 'No courses available')}</p>
      </div>
    )
  }

  // Use mastery overview data (from KnowledgePointMastery) for mastery path card
  const masteryScore = masteryOverview?.avg_mastery ?? 0
  const masteryLevel = getMasteryLevel(masteryScore)

  // Current chapter from masteryOverview (order_index)
  const currentChapterData = masteryOverview?.chapters?.find(
    ch => ch.order_index === masteryOverview.current_chapter
  )
  const currentChapterTitle = currentChapterData?.title || (masteryOverview?.current_chapter ? `第${masteryOverview.current_chapter}章` : t('准备开始', 'Ready to start'))

  // Progress matches avg_mastery (same as grid display)
  const progress = Math.round(masteryScore)

  // 精进之路：直接进入 mastery 页面
  const handleMasteryStart = () => {
    setIsNavigating('mastery')
    router.push(`/mastery/${currentCourse.course_id}`)
  }

  // 挑战之路：显示难度选择
  const handleChallengeStart = () => {
    setShowDifficultyModal(true)
  }

  // 选择难度后直接跳转到挑战页面，初始化逻辑由 arena 页面负责
  const handleDifficultySelect = (difficulty: number) => {
    setSelectedDifficulty(difficulty)
    setIsNavigating('challenge')
    router.push(`/arena?difficulty=${difficulty}`)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-card rounded-2xl border border-border p-5 h-full flex flex-col overflow-hidden"
    >
      {/* Header with course switcher */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <CourseSwitcher
          courses={courses}
          currentCourseId={currentCourseId}
          onSwitch={onSwitchCourse}
          lang={lang}
        />
      </div>

      {/* Dual Path Cards */}
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="flex-1 grid grid-cols-2 gap-4 min-h-0"
      >
        {/* Mastery Path Card */}
        <motion.div
          variants={staggerItem}
          whileHover={{ scale: 1.01, transition: { duration: 0.2 } }}
          className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 rounded-xl border border-amber-500/20 p-4 flex flex-col overflow-hidden"
        >
          <div className="flex items-center gap-2 mb-3 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
              <Trophy className="w-4 h-4 text-amber-500" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">{t('精进之路', 'Mastery')}</h4>
              <p className="text-xs text-muted-foreground">{t('章节模式', 'Chapter-based')}</p>
            </div>
          </div>

          {/* Content area - flex-1 to push button to bottom */}
          <div className="flex-1 flex flex-col min-h-0">
            {/* Current chapter & section - 横向并排显示 */}
            <div className="flex items-start gap-3 mb-2">
              {/* 当前章节 */}
              <div className="flex-1 min-w-0">
                <p className="text-xs text-muted-foreground mb-0.5">{t('当前章节', 'Current Chapter')}</p>
                <p className="text-sm font-medium text-foreground truncate">
                  {currentChapterTitle}
                </p>
              </div>
              {/* 当前小节 */}
              {currentCourse.current_section && (
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-muted-foreground mb-0.5">{t('当前小节', 'Current Section')}</p>
                  <p className="text-sm font-medium text-amber-600 dark:text-amber-400 truncate">
                    {currentCourse.current_section}
                  </p>
                </div>
              )}
            </div>

            {/* Progress bar */}
            <div className="mb-3 mt-auto">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>{t('掌握度', 'Mastery')}</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 bg-amber-500/20 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>

          {/* Action button */}
          <button type="button"
            onClick={handleMasteryStart}
            disabled={isNavigating === 'mastery'}
            className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg font-medium text-sm bg-gradient-to-r from-amber-500 to-amber-400 text-white hover:shadow-lg hover:shadow-amber-500/25 transition-all disabled:opacity-70 flex-shrink-0"
          >
            {isNavigating === 'mastery' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                {t('开始学习', 'Start')}
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </motion.div>

        {/* Challenge Path Card */}
        <motion.div
          variants={staggerItem}
          whileHover={{ scale: 1.01, transition: { duration: 0.2 } }}
          className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-xl border border-blue-500/20 p-4 flex flex-col overflow-hidden"
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <Swords className="w-4 h-4 text-blue-500" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">{t('挑战之路', 'Challenge')}</h4>
              <p className="text-xs text-muted-foreground">{t('难度模式', 'Difficulty-based')}</p>
            </div>
          </div>

          {currentCourse.arena_tier ? (
            <>
              {/* Tier display with recent exercises on the right */}
              <div className="flex-1 flex gap-3">
                {/* Left: Current tier info */}
                <div className="flex-shrink-0">
                  <p className="text-xs text-muted-foreground mb-1">{t('当前段位', 'Current Tier')}</p>
                  <div className="flex items-center gap-2">
                    <span className="w-8 h-8 flex items-center justify-center">
                      {getTierConfig(currentCourse.arena_tier)?.icon}
                    </span>
                    <div>
                      <p className="text-sm font-medium" style={{ color: TIER_COLORS[currentCourse.arena_tier] || '#CD7F32' }}>
                        {getTierFullName(currentCourse.arena_tier, currentCourse.arena_sub_tier)}
                      </p>
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                        {currentCourse.arena_stars !== null ? (
                          <>
                            <Star className="w-3 h-3 text-amber-500 fill-amber-500" />
                            <span className="font-medium">{currentCourse.arena_stars}</span> {t('星', 'stars')}
                          </>
                        ) : (
                          t('开始挑战获取星星', 'Start to earn stars')
                        )}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Right: Recent exercises */}
                {recentExercises.length > 0 && (
                  <div className="flex-1 min-w-0 pl-3 border-l border-blue-500/20">
                    <p className="text-xs text-muted-foreground mb-1">{t('最近练习', 'Recent')}</p>
                    <div className="space-y-1">
                      {recentExercises.slice(0, 2).map((ex, idx) => (
                        <div key={idx} className="flex items-center gap-1.5 text-xs">
                          {ex.isCorrect ? (
                            <CheckCircle className="w-3 h-3 text-emerald-500 flex-shrink-0" />
                          ) : (
                            <XCircle className="w-3 h-3 text-red-500 flex-shrink-0" />
                          )}
                          <span className="truncate text-foreground">
                            {ex.stageName}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              {/* 最近练习 - 没有段位时显示 */}
              {recentExercises.length > 0 ? (
                <div className="flex-1 w-full space-y-1.5">
                  <p className="text-xs text-muted-foreground mb-2">{t('最近练习', 'Recent Exercises')}</p>
                  {recentExercises.slice(0, 3).map((ex, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs">
                      {ex.isCorrect ? (
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                      )}
                      <span className="truncate text-foreground">
                        {ex.stageName}
                        <span className={ex.isCorrect ? 'text-emerald-500 ml-1' : 'text-red-500 ml-1'}>
                          {ex.isCorrect ? t('正确', 'Correct') : t('错误', 'Wrong')}
                        </span>
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <p className="text-xs text-muted-foreground text-center">
                    {t('挑战获取段位', 'Challenge to earn tier')}
                  </p>
                </div>
              )}
            </>
          )}

          {/* Action button */}
          <button type="button"
            onClick={handleChallengeStart}
            disabled={isNavigating === 'challenge'}
            className="w-full mt-auto flex items-center justify-center gap-1.5 py-2 rounded-lg font-medium text-sm bg-gradient-to-r from-blue-500 to-blue-400 text-white hover:shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-70 flex-shrink-0"
          >
            {isNavigating === 'challenge' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                {t('开始挑战', 'Start Challenge')}
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </motion.div>
      </motion.div>

      {/* Difficulty Selection Modal */}
      <AnimatePresence>
        {showDifficultyModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          >
            <motion.div
              variants={scaleIn}
              initial="initial"
              animate="animate"
              exit="exit"
              className="bg-card rounded-2xl border border-border p-6 w-80 shadow-xl"
            >
            <h3 className="text-lg font-semibold text-foreground mb-4 text-center">
              {t('选择难度', 'Select Difficulty')}
            </h3>
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((level) => (
                <motion.button
                  key={level}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleDifficultySelect(level)}
                  disabled={isNavigating === 'challenge'}
                  className={`w-full py-3 rounded-xl font-medium text-sm transition-all flex items-center justify-between px-4 ${
                    level === 1
                      ? 'bg-green-500/20 text-green-600 dark:text-green-400 hover:bg-green-500/30'
                      : level === 2
                      ? 'bg-lime-500/20 text-lime-600 dark:text-lime-400 hover:bg-lime-500/30'
                      : level === 3
                      ? 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 hover:bg-yellow-500/30'
                      : level === 4
                      ? 'bg-orange-500/20 text-orange-600 dark:text-orange-400 hover:bg-orange-500/30'
                      : 'bg-red-500/20 text-red-600 dark:text-red-400 hover:bg-red-500/30'
                  } ${isNavigating === 'challenge' ? 'opacity-50' : ''}`}
                >
                  <span className="flex items-center gap-2">
                    <span className="flex">
                      {Array.from({ length: level }).map((_, i) => (
                        <Star key={i} className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                      ))}
                    </span>
                    {t(`${level}星难度`, `${level}-Star Difficulty`)}
                  </span>
                  <span className="text-xs opacity-70">
                    {level === 1 ? '+10' : level === 2 ? '+20' : level === 3 ? '+35' : level === 4 ? '+50' : '+70'}
                  </span>
                </motion.button>
              ))}
            </div>
            <button type="button"
              onClick={() => setShowDifficultyModal(false)}
              className="w-full mt-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {t('取消', 'Cancel')}
            </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
