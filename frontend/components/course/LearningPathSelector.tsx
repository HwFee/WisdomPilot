'use client'

import { Map, Zap, ArrowRight, Lock, Trophy, Swords, Crown, TrendingUp } from 'lucide-react'
import type { Tier, MasteryLevel } from '@/types/api'
import { TIER_ICONS, TIER_NAMES, MASTERY_LEVEL_COLORS } from '@/lib/api'

interface MasteryProgress {
  currentChapter: string
  completedChapters: number
  totalChapters: number
  masteryPoints: number
  avgMastery: number
  currentMasteryLevel: MasteryLevel
}

interface ArenaProgress {
  tier: Tier
  score: number
  highestDifficulty: number
  totalChallenges: number
  wins: number
}

interface LearningPathSelectorProps {
  courseId: number
  masteryProgress?: MasteryProgress
  arenaProgress?: ArenaProgress
  onMasteryPathStart: () => void
  onChallengePathStart: () => void
  masteryPathUnlocked?: boolean
  challengePathUnlocked?: boolean
  lang?: 'zh' | 'en'
}

export function LearningPathSelector({
  courseId,
  masteryProgress,
  arenaProgress,
  onMasteryPathStart,
  onChallengePathStart,
  masteryPathUnlocked = true,
  challengePathUnlocked = true,
  lang = 'zh',
}: LearningPathSelectorProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const masteryPercent = masteryProgress
    ? Math.round((masteryProgress.completedChapters / masteryProgress.totalChapters) * 100)
    : 0

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Mastery Path (精进之路) */}
      <div className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 rounded-2xl border border-amber-500/20 p-6 relative overflow-hidden flex flex-col">
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2"></div>

        <div className="relative flex flex-col h-full">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center flex-shrink-0">
              <Trophy className="w-6 h-6 text-amber-500" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                {t('精进之路', 'Mastery Path')}
              </h3>
              <p className="text-sm text-muted-foreground">
                {t('章节模式 · 循序渐进', 'Chapter-based learning')}
              </p>
            </div>
          </div>

          <div className="flex-1">
            {masteryProgress ? (
              <>
                {/* Current progress */}
                <div className="mb-4 p-3 bg-amber-500/10 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">
                      {t('当前进度：', 'Current: ')}
                      <span className="font-medium text-amber-600">{masteryProgress.currentChapter}</span>
                    </span>
                    <span className={`text-xs font-medium ${MASTERY_LEVEL_COLORS[masteryProgress.currentMasteryLevel] || 'text-muted-foreground'}`}>
                      {masteryProgress.currentMasteryLevel}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{t('掌握分数', 'Mastery Score')}</span>
                    <span className="font-medium text-foreground">{(masteryProgress.masteryPoints ?? 0).toFixed(0)}</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-muted-foreground mb-1">
                    <span>{t('章节完成度', 'Chapter Progress')}</span>
                    <span>
                      {masteryProgress.completedChapters}/{masteryProgress.totalChapters} ({masteryPercent}%)
                    </span>
                  </div>
                  <div className="h-2 bg-amber-500/20 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all"
                      style={{ width: `${masteryPercent}%` }}
                    />
                  </div>
                </div>
              </>
            ) : (
              <div className="mb-4 text-sm text-muted-foreground">
                <p>{t('开始你的精进之旅', 'Start your mastery journey')}</p>
              </div>
            )}
          </div>

          <button
            onClick={onMasteryPathStart}
            disabled={!masteryPathUnlocked}
            className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-all ${
              masteryPathUnlocked
                ? 'bg-gradient-to-r from-amber-500 to-amber-400 text-white hover:shadow-lg hover:shadow-amber-500/25 hover-lift'
                : 'bg-muted text-muted-foreground cursor-not-allowed'
            }`}
          >
            {masteryPathUnlocked ? (
              <>
                <Map className="w-4 h-4" />
                {masteryProgress?.completedChapters === 0
                  ? t('开始学习', 'Start Learning')
                  : t('继续精进', 'Continue Mastery')}
                <ArrowRight className="w-4 h-4" />
              </>
            ) : (
              <>
                <Lock className="w-4 h-4" />
                {t('解锁中...', 'Unlocking...')}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Challenge Path (挑战之路) */}
      <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-2xl border border-blue-500/20 p-6 relative overflow-hidden flex flex-col">
        {/* Background decoration */}
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl translate-y-1/2 -translate-x-1/2"></div>

        <div className="relative flex flex-col h-full">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center flex-shrink-0">
              <Swords className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                {t('挑战之路', 'Challenge Path')}
              </h3>
              <p className="text-sm text-muted-foreground">
                {t('难度模式 · 竞技打榜', 'Difficulty-based challenges')}
              </p>
            </div>
          </div>

          <div className="flex-1">
            {arenaProgress ? (
              <>
                {/* Tier and score */}
                <div className="mb-4 p-3 bg-blue-500/10 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{TIER_ICONS[arenaProgress.tier]}</span>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {TIER_NAMES[arenaProgress.tier]}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {t('段位', 'Tier')}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-blue-500">
                        {(arenaProgress.score ?? 0).toFixed(0)}
                      </p>
                      <p className="text-xs text-muted-foreground">{t('积分', 'Score')}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      {arenaProgress.totalChallenges} {t('场', 'games')}
                    </span>
                    <span>
                      {arenaProgress.wins} {t('胜', 'wins')}
                    </span>
                  </div>
                </div>

                {/* Difficulty levels */}
                <div className="mb-4">
                  <p className="text-xs text-muted-foreground mb-2">{t('难度等级', 'Difficulty Level')}</p>
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <div
                        key={level}
                        className={`flex-1 h-6 rounded flex items-center justify-center text-xs font-medium transition-all ${
                          level <= arenaProgress.highestDifficulty
                            ? 'bg-blue-500 text-white'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {level}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="mb-4 text-sm text-muted-foreground">
                  <p>{t('挑战随机题库，争夺竞技榜排名', 'Challenge for arena ranking')}</p>
                </div>

                {/* Difficulty preview */}
                <div className="mb-4">
                  <p className="text-xs text-muted-foreground mb-2">{t('难度等级', 'Difficulty Level')}</p>
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <div
                        key={level}
                        className="flex-1 h-6 rounded bg-muted flex items-center justify-center text-xs font-medium text-muted-foreground"
                      >
                        {level}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>

          <button
            onClick={onChallengePathStart}
            disabled={!challengePathUnlocked}
            className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-all ${
              challengePathUnlocked
                ? 'bg-gradient-to-r from-blue-500 to-blue-400 text-white hover:shadow-lg hover:shadow-blue-500/25 hover-lift'
                : 'bg-muted/50 text-muted-foreground cursor-not-allowed'
            }`}
          >
            {challengePathUnlocked ? (
              <>
                <Zap className="w-4 h-4" />
                {t('开始挑战', 'Start Challenge')}
                <ArrowRight className="w-4 h-4" />
              </>
            ) : (
              <>
                <Lock className="w-4 h-4" />
                {t('解锁中...', 'Unlocking...')}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// Export the old name for backward compatibility
export { LearningPathSelector as ChallengeModeSelector }
