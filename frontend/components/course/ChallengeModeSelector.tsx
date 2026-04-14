'use client'

import { Map, Zap, ArrowRight, Lock } from 'lucide-react'

interface ChallengeModeSelectorProps {
  currentChapter?: string
  progress: number
  onMainLineStart: () => void
  onSideLineStart: () => void
  mainLineUnlocked?: boolean
  sideLineUnlocked?: boolean
  lang?: 'zh' | 'en'
}

export function ChallengeModeSelector({
  currentChapter,
  progress,
  onMainLineStart,
  onSideLineStart,
  mainLineUnlocked = true,
  sideLineUnlocked = true,
  lang = 'zh',
}: ChallengeModeSelectorProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
      {/* Main Line Challenge - 65% width */}
      <div className="lg:col-span-3 bg-gradient-to-br from-primary/10 to-primary/5 rounded-2xl border border-primary/20 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
            <Map className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">{t('主线闯关', 'Main Line')}</h3>
            <p className="text-sm text-muted-foreground">
              {t('章节顺序，循序渐进', 'Sequential chapters')}
            </p>
          </div>
        </div>

        {currentChapter && (
          <div className="mb-4 text-sm">
            <span className="text-muted-foreground">{t('当前进度：', 'Current: ')}</span>
            <span className="font-medium text-primary">{currentChapter}</span>
          </div>
        )}

        <div className="mb-4">
          <div className="flex justify-between text-sm text-muted-foreground mb-1">
            <span>{t('章节完成度', 'Chapter Progress')}</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 bg-primary/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <button
          onClick={onMainLineStart}
          disabled={!mainLineUnlocked}
          className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-colors ${
            mainLineUnlocked
              ? 'bg-primary text-primary-foreground hover:bg-primary-600 shadow-lg shadow-primary/25'
              : 'bg-muted text-muted-foreground cursor-not-allowed'
          }`}
        >
          {mainLineUnlocked ? (
            <>
              {t('继续闯关', 'Continue Challenge')}
              <ArrowRight className="w-4 h-4" />
            </>
          ) : (
            <>
              <Lock className="w-4 h-4" />
              {t('完成上一章解锁', 'Complete previous chapter')}
            </>
          )}
        </button>
      </div>

      {/* Side Line Challenge - 35% width */}
      <div className="lg:col-span-2 bg-card rounded-2xl border border-border p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
            <Zap className="w-6 h-6 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">{t('支线挑战', 'Side Challenge')}</h3>
            <p className="text-sm text-muted-foreground">
              {t('难度分级，自由选择', 'Difficulty levels')}
            </p>
          </div>
        </div>

        <div className="mb-4 text-sm text-muted-foreground">
          <p>{t('挑战随机题库，测试综合能力', 'Challenge random problems')}</p>
        </div>

        {/* Difficulty selector preview */}
        <div className="flex items-center gap-2 mb-4">
          {[1, 2, 3, 4, 5].map((level) => (
            <div
              key={level}
              className="flex-1 h-8 rounded bg-muted flex items-center justify-center text-xs font-medium text-muted-foreground"
            >
              L{level}
            </div>
          ))}
        </div>

        <button
          onClick={onSideLineStart}
          disabled={!sideLineUnlocked}
          className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-colors ${
            sideLineUnlocked
              ? 'bg-muted text-foreground hover:bg-muted/80 border border-border'
              : 'bg-muted/50 text-muted-foreground cursor-not-allowed'
          }`}
        >
          {sideLineUnlocked ? (
            <>
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
  )
}
