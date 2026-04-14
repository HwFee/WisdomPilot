'use client'

import { Trophy, Swords, ChevronRight, Crown, Medal, BookOpen, CheckCircle, XCircle } from 'lucide-react'
import { CourseSwitcher } from './CourseSwitcher'
import { useRouter } from 'next/navigation'

interface RecentExercise {
  stageName: string
  isCorrect: boolean
  time?: string
}

interface Course {
  course_id: number
  course_code: string
  course_name: string
  progress: number
  completed_stages: number
  total_stages: number
  current_chapter: string | null
  mastery_score: number | null
  arena_tier: string | null
  arena_score: number | null
}

interface CurrentLearningPanelProps {
  courses: Course[]
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
}

const TIER_ICONS: Record<string, string> = {
  bronze: '🥉',
  silver: '🥈',
  gold: '🥇',
  platinum: '💎',
  diamond: '👑',
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

  const currentCourse = courses.find(c => c.course_id === currentCourseId) || courses[0]

  if (!currentCourse) {
    return (
      <div className="bg-card rounded-2xl border border-border p-6 h-full flex items-center justify-center">
        <p className="text-muted-foreground">{t('暂无课程数据', 'No courses available')}</p>
      </div>
    )
  }

  const masteryLevel = getMasteryLevel(currentCourse.mastery_score)
  const hasProgress = currentCourse.progress > 0

  const handleMasteryStart = () => {
    router.push(`/courses/${currentCourse.course_id}`)
  }

  const handleChallengeStart = () => {
    router.push(`/challenge/${currentCourse.course_id}`)
  }

  return (
    <div className="bg-card rounded-2xl border border-border p-5 h-full flex flex-col overflow-hidden">
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
      <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
        {/* Mastery Path Card */}
        <div className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 rounded-xl border border-amber-500/20 p-4 flex flex-col overflow-hidden">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
              <Trophy className="w-4 h-4 text-amber-500" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">{t('精进之路', 'Mastery')}</h4>
              <p className="text-xs text-muted-foreground">{t('章节模式', 'Chapter-based')}</p>
            </div>
          </div>

          {hasProgress ? (
            <>
              {/* Current chapter */}
              <div className="mb-3 flex-1">
                <p className="text-xs text-muted-foreground mb-1">{t('当前章节', 'Current Chapter')}</p>
                <p className="text-sm font-medium text-foreground truncate">
                  {currentCourse.current_chapter || t('准备开始', 'Ready to start')}
                </p>
              </div>

              {/* Progress bar */}
              <div className="mb-3">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>{t('进度', 'Progress')}</span>
                  <span>{currentCourse.progress}%</span>
                </div>
                <div className="h-2 bg-amber-500/20 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all"
                    style={{ width: `${currentCourse.progress}%` }}
                  />
                </div>
              </div>

              {/* Mastery score */}
              {currentCourse.mastery_score !== null && (
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="text-muted-foreground">{t('掌握分数', 'Mastery Score')}</span>
                  <span className={`font-medium ${masteryLevel.color}`}>
                    {currentCourse.mastery_score.toFixed(0)} ({masteryLevel.name})
                  </span>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center">
              {recentExercises.length > 0 ? (
                <div className="w-full space-y-1.5">
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
                <p className="text-xs text-muted-foreground text-center">
                  {t('开始你的学习之旅', 'Start your learning journey')}
                </p>
              )}
            </div>
          )}

          {/* Action button */}
          <button
            onClick={handleMasteryStart}
            className="w-full mt-auto flex items-center justify-center gap-1.5 py-2 rounded-lg font-medium text-sm bg-gradient-to-r from-amber-500 to-amber-400 text-white hover:shadow-lg hover:shadow-amber-500/25 transition-all"
          >
            {hasProgress ? t('继续精进', 'Continue') : t('开始学习', 'Start')}
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Challenge Path Card */}
        <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-xl border border-blue-500/20 p-4 flex flex-col overflow-hidden">
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
              {/* Tier display */}
              <div className="mb-3 flex-1">
                <p className="text-xs text-muted-foreground mb-1">{t('当前段位', 'Current Tier')}</p>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{TIER_ICONS[currentCourse.arena_tier] || '🥉'}</span>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {TIER_NAMES[currentCourse.arena_tier] || '青铜'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {currentCourse.arena_score?.toFixed(0) || 0} {t('积分', 'points')}
                    </p>
                  </div>
                </div>
              </div>

              {/* Difficulty levels */}
              <div className="mb-3">
                <p className="text-xs text-muted-foreground mb-1">{t('难度解锁', 'Difficulty Unlocked')}</p>
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <div
                      key={level}
                      className="flex-1 h-5 rounded flex items-center justify-center text-xs font-medium bg-blue-500/20 text-blue-600 dark:text-blue-400"
                    >
                      {level}
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-xs text-muted-foreground text-center">
                {t('挑战获取积分', 'Challenge to earn points')}
              </p>
            </div>
          )}

          {/* Action button */}
          <button
            onClick={handleChallengeStart}
            className="w-full mt-auto flex items-center justify-center gap-1.5 py-2 rounded-lg font-medium text-sm bg-gradient-to-r from-blue-500 to-blue-400 text-white hover:shadow-lg hover:shadow-blue-500/25 transition-all"
          >
            {t('开始挑战', 'Start Challenge')}
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
