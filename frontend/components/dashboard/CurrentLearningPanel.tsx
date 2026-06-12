'use client'

import { useState, useEffect } from 'react'
import { Trophy, Swords, ChevronRight, CheckCircle, XCircle, Loader2, Star } from 'lucide-react'
import { CourseSwitcher } from './CourseSwitcher'
import { useRouter } from 'next/navigation'
import { getMasteryOverview, type MasteryOverviewResponse } from '@/lib/api/learning-path'
import { getStoredToken } from '@/lib/api'
import type { CourseProgress } from '@/lib/api/courses'
import { getTierConfig } from '@/lib/icons/tier-icons'

interface RecentExercise {
  stageName: string
  isCorrect: boolean
  time?: string
}

const EMPTY_EXERCISE_ARRAY: RecentExercise[] = []

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
  { min: 0, max: 30, name: '入门' },
  { min: 31, max: 50, name: '学习' },
  { min: 51, max: 70, name: '练习' },
  { min: 71, max: 85, name: '熟练' },
  { min: 86, max: 100, name: '精通' },
]

function getMasteryLevel(score: number | null) {
  if (score === null) return MASTERY_LEVELS[0]
  return MASTERY_LEVELS.find(l => score >= l.min && score <= l.max) || MASTERY_LEVELS[0]
}

export function CurrentLearningPanel({
  courses,
  currentCourseId,
  onSwitchCourse,
  recentExercises = EMPTY_EXERCISE_ARRAY,
  lang = 'zh'
}: CurrentLearningPanelProps) {
  const { push } = useRouter()
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const [isNavigating, setIsNavigating] = useState<'mastery' | 'challenge' | null>(null)
  const [showDifficultyModal, setShowDifficultyModal] = useState(false)
  const [masteryOverview, setMasteryOverview] = useState<MasteryOverviewResponse | null>(null)

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
      <div className="bg-card border border-border p-6 h-full flex items-center justify-center">
        <p className="text-muted-foreground">{t('暂无课程数据', 'No courses available')}</p>
      </div>
    )
  }

  const masteryScore = masteryOverview?.avg_mastery ?? 0
  const masteryLevel = getMasteryLevel(masteryScore)

  const currentChapterData = masteryOverview?.chapters?.find(
    ch => ch.order_index === masteryOverview.current_chapter
  )
  const currentChapterTitle = currentChapterData?.title || (masteryOverview?.current_chapter ? `第${masteryOverview.current_chapter}章` : t('准备开始', 'Ready to start'))

  const progress = Math.round(masteryScore)

  const handleMasteryStart = () => {
    setIsNavigating('mastery')
    push(`/mastery/${currentCourse.course_id}`)
  }

  const handleChallengeStart = () => {
    setShowDifficultyModal(true)
  }

  const handleDifficultySelect = (difficulty: number) => {
    setIsNavigating('challenge')
    push(`/arena?difficulty=${difficulty}`)
  }

  const DIFFICULTY_STYLES = [
    { label: '入门', color: 'text-emerald-600 bg-emerald-50 border-emerald-200', reward: 10 },
    { label: '普及', color: 'text-lime-600 bg-lime-50 border-lime-200', reward: 20 },
    { label: '提高', color: 'text-amber-600 bg-amber-50 border-amber-200', reward: 35 },
    { label: '省选', color: 'text-orange-600 bg-orange-50 border-orange-200', reward: 50 },
    { label: 'NOI', color: 'text-red-600 bg-red-50 border-red-200', reward: 70 },
  ]

  return (
    <div className="bg-card border border-border p-5 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <CourseSwitcher
          courses={courses}
          currentCourseId={currentCourseId}
          onSwitch={onSwitchCourse}
          lang={lang}
        />
      </div>

      {/* Dual Path Cards */}
      <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
        {/* Mastery Path Card */}
        <div className="bg-secondary border border-border p-4 flex flex-col">
          <div className="flex items-center gap-2 mb-3 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center">
              <Trophy className="w-4 h-4 text-foreground" strokeWidth={1.5} />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">{t('精进之路', 'Mastery')}</h4>
              <p className="text-xs text-muted-foreground">{t('章节模式', 'Chapter-based')}</p>
            </div>
          </div>

          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex items-start gap-3 mb-2">
              <div className="flex-1 min-w-0">
                <p className="text-xs text-muted-foreground mb-0.5">{t('当前章节', 'Current Chapter')}</p>
                <p className="text-sm font-medium text-foreground truncate">
                  {currentChapterTitle}
                </p>
              </div>
              {currentCourse.current_section && (
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-muted-foreground mb-0.5">{t('当前小节', 'Current Section')}</p>
                  <p className="text-sm font-medium text-foreground truncate">
                    {currentCourse.current_section}
                  </p>
                </div>
              )}
            </div>

            <div className="mb-3 mt-auto">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>{t('掌握度', 'Mastery')}</span>
                <span>{progress}% · {masteryLevel.name}</span>
              </div>
              <div className="h-1.5 bg-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-foreground rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>

          <button type="button"
            onClick={handleMasteryStart}
            disabled={isNavigating === 'mastery'}
            className="w-full flex items-center justify-center gap-1.5 py-2 font-medium text-sm bg-foreground text-background hover:bg-foreground/90 transition-colors disabled:opacity-70 flex-shrink-0"
          >
            {isNavigating === 'mastery' ? (
              <Loader2 className="w-4 h-4 animate-spin" strokeWidth={1.5} />
            ) : (
              <>
                {t('开始学习', 'Start')}
                <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
              </>
            )}
          </button>
        </div>

        {/* Challenge Path Card */}
        <div className="bg-secondary border border-border p-4 flex flex-col">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center">
              <Swords className="w-4 h-4 text-foreground" strokeWidth={1.5} />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">{t('挑战之路', 'Challenge')}</h4>
              <p className="text-xs text-muted-foreground">{t('难度模式', 'Difficulty-based')}</p>
            </div>
          </div>

          {currentCourse.arena_tier ? (
            <div className="flex-1 flex gap-3 min-h-0">
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
                          <Star className="w-3 h-3 text-amber-500 fill-amber-500" strokeWidth={1.5} />
                          <span className="font-medium">{currentCourse.arena_stars}</span> {t('星', 'stars')}
                        </>
                      ) : (
                        t('开始挑战获取星星', 'Start to earn stars')
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {recentExercises.length > 0 && (
                <div className="flex-1 min-w-0 pl-3 border-l border-border">
                  <p className="text-xs text-muted-foreground mb-1">{t('最近练习', 'Recent')}</p>
                  <div className="flex flex-col gap-y-1">
                    {recentExercises.slice(0, 2).map((ex) => (
                      <div key={`${ex.stageName}-${ex.time || ''}`} className="flex items-center gap-1.5 text-xs">
                        {ex.isCorrect ? (
                          <CheckCircle className="w-3 h-3 text-emerald-500 flex-shrink-0" strokeWidth={1.5} />
                        ) : (
                          <XCircle className="w-3 h-3 text-red-500 flex-shrink-0" strokeWidth={1.5} />
                        )}
                        <span className="truncate text-foreground">{ex.stageName}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <>
              {recentExercises.length > 0 ? (
                <div className="flex-1 w-full gap-y-1.5">
                  <p className="text-xs text-muted-foreground mb-2">{t('最近练习', 'Recent Exercises')}</p>
                  {recentExercises.slice(0, 3).map((ex) => (
                    <div key={`${ex.stageName}-${ex.time || ''}`} className="flex items-center gap-2 text-xs">
                      {ex.isCorrect ? (
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" strokeWidth={1.5} />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" strokeWidth={1.5} />
                      )}
                      <span className="truncate text-foreground">
                        {ex.stageName}
                        <span className={ex.isCorrect ? 'text-emerald-600 ml-1' : 'text-red-600 ml-1'}>
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

          <button type="button"
            onClick={handleChallengeStart}
            disabled={isNavigating === 'challenge'}
            className="w-full mt-auto flex items-center justify-center gap-1.5 py-2 font-medium text-sm border border-foreground text-foreground hover:bg-foreground hover:text-background transition-colors disabled:opacity-70 flex-shrink-0"
          >
            {isNavigating === 'challenge' ? (
              <Loader2 className="w-4 h-4 animate-spin" strokeWidth={1.5} />
            ) : (
              <>
                {t('开始挑战', 'Start Challenge')}
                <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Difficulty Selection Modal */}
      {showDifficultyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-card border border-border p-6 w-80">
            <h3 className="text-lg font-semibold text-foreground mb-4 text-center">
              {t('选择难度', 'Select Difficulty')}
            </h3>
            <div className="flex flex-col gap-y-2">
              {[1, 2, 3, 4, 5].map((level) => {
                const style = DIFFICULTY_STYLES[level - 1]
                return (
                  <button
                    key={level}
                    onClick={() => handleDifficultySelect(level)}
                    disabled={isNavigating === 'challenge'}
                    className={`w-full py-3 text-sm font-medium transition-colors flex items-center justify-between px-4 border ${style.color} hover:opacity-80 ${isNavigating === 'challenge' ? 'opacity-50' : ''}`}
                  >
                    <span className="flex items-center gap-2">
                      <span className="flex">
                        {Array.from({ length: level }).map((_, i) => (
                          <Star key={`learning-${i}`} className="w-3.5 h-3.5 text-amber-500 fill-amber-500" strokeWidth={1.5} />
                        ))}
                      </span>
                      {style.label}
                    </span>
                    <span className="text-xs opacity-70">
                      +{style.reward}
                    </span>
                  </button>
                )
              })}
            </div>
            <button type="button"
              onClick={() => setShowDifficultyModal(false)}
              className="w-full mt-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {t('取消', 'Cancel')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
