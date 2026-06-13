'use client'

import { Trophy, Star, Zap, ArrowRight, Target } from 'lucide-react'
import { Panel, PanelHeader, CourseListItem } from '@/components/layout'
import { Button } from '@/components/ui/button'
import type { CourseProgress } from '@/lib/api/courses'
import type { TierInfo } from '@/types/api'

interface CurrentLearningPanelProps {
  courses: CourseProgress[]
  tierInfo?: TierInfo | null
  lang?: 'zh' | 'en'
  onEnterArena?: () => void
}

// Mirrors backend/app/core/tier_config.py stars_per_tier for each rank.
const TIER_STARS_CONFIG: Record<string, { starsNeeded: number }> = {
  bronze: { starsNeeded: 3 },
  silver: { starsNeeded: 3 },
  gold: { starsNeeded: 4 },
  platinum: { starsNeeded: 4 },
  diamond: { starsNeeded: 5 },
  master: { starsNeeded: 5 },
  king: { starsNeeded: 0 },
}

export function CurrentLearningPanel({
  courses,
  tierInfo,
  lang = 'zh',
  onEnterArena,
}: CurrentLearningPanelProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const isKing = tierInfo?.tier === 'king'
  const starsNeeded = isKing
    ? Math.max(tierInfo?.stars ?? 0, 1)
    : (TIER_STARS_CONFIG[tierInfo?.tier ?? '']?.starsNeeded ?? 3)
  const starProgress = isKing
    ? 100
    : Math.min(
        100,
        Math.max(0, ((tierInfo?.stars ?? 0) / starsNeeded) * 100)
      )

  return (
    <Panel>
      <PanelHeader
        title={t('学习进度', 'Learning Progress')}
        count={t(`${courses.length} 门课程`, `${courses.length} courses`)}
      />

      {/* Block 1: 精进之路 */}
      <div>
        <div className="px-8 py-4 border-b border-border bg-muted/20">
          <h4 className="text-xs font-semibold uppercase tracking-[1.5px] text-muted-foreground flex items-center gap-2">
            <svg className="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
            {t('精进之路', 'Mastery Path')}
          </h4>
        </div>
        {courses.length === 0 ? (
          <div className="px-8 py-6 text-sm text-muted-foreground">
            {t('暂无课程数据', 'No courses available')}
          </div>
        ) : (
          courses.map((course, idx) => (
            <CourseListItem
              key={course.course_id}
              num={String(idx + 1).padStart(2, '0')}
              name={course.course_name}
              chapter={course.current_chapter || course.current_section || t('准备开始', 'Ready to start')}
              percent={Math.round(course.progress)}
              href={`/mastery/${course.course_id}`}
            />
          ))
        )}
      </div>

      {/* Block 2: 挑战之路 */}
      <div className="border-t border-border bg-muted/20">
        <div className="px-8 py-4 border-b border-border">
          <h4 className="text-xs font-semibold uppercase tracking-[1.5px] text-muted-foreground flex items-center gap-2">
            <Trophy className="size-3.5" strokeWidth={1.5} />
            {t('挑战之路', 'Arena Path')}
          </h4>
        </div>
        <div className="px-8 py-5">
          {tierInfo ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className="size-10 shrink-0 rounded-md flex items-center justify-center border"
                    style={{
                      backgroundColor: `${tierInfo.color}15`,
                      borderColor: `${tierInfo.color}30`,
                      color: tierInfo.color,
                    }}
                  >
                    <Trophy className="size-5" strokeWidth={1.5} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold truncate">{tierInfo.full_name}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {t('当前段位', 'Current tier')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-xs font-medium shrink-0">
                  <Star className="size-3.5 fill-amber-500 text-amber-500" strokeWidth={1.5} />
                  <span>{tierInfo.stars}{!isKing && <span className="text-muted-foreground">/{starsNeeded}</span>}</span>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="w-full h-[3px] bg-border relative">
                    <div
                      className="absolute left-0 top-0 bottom-0 bg-foreground transition-all duration-500 ease-out"
                      style={{ width: `${starProgress}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1.5">
                    {isKing
                      ? t('已抵达最高段位', 'Reached highest tier')
                      : t(`再获得 ${Math.max(0, starsNeeded - tierInfo.stars)} 星升级`, `${Math.max(0, starsNeeded - tierInfo.stars)} more stars to promote`)}
                  </p>
                </div>
              </div>

              <Button
                type="button"
                onClick={onEnterArena}
                className="w-full h-9 gap-2 rounded-md bg-foreground text-background hover:bg-foreground/90"
              >
                <Zap className="size-4" strokeWidth={1.5} />
                {t('进入挑战之路', 'Enter Arena')}
                <ArrowRight className="size-4" strokeWidth={1.5} />
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-md bg-muted border border-border flex items-center justify-center text-muted-foreground">
                  <Target className="size-5" strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-sm font-semibold">{t('挑战之路', 'Arena Path')}</p>
                  <p className="text-xs text-muted-foreground">{t('测试实战能力，提升段位', 'Test your skills and climb tiers')}</p>
                </div>
              </div>
              <Button
                type="button"
                onClick={onEnterArena}
                className="w-full h-9 gap-2 rounded-md bg-foreground text-background hover:bg-foreground/90"
              >
                <Zap className="size-4" strokeWidth={1.5} />
                {t('进入挑战之路', 'Enter Arena')}
                <ArrowRight className="size-4" strokeWidth={1.5} />
              </Button>
            </div>
          )}
        </div>
      </div>
    </Panel>
  )
}
