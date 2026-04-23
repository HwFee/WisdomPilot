'use client'

import { Brain, TrendingUp, ArrowRight } from 'lucide-react'

interface KnowledgePoint {
  name: string
  mastery: number // 0-100
  courseId?: number
}

interface KnowledgeMasteryProps {
  courseName: string
  knowledgePoints: KnowledgePoint[]
  onLearnClick?: (courseId?: number) => void
  lang?: 'zh' | 'en'
  compact?: boolean
}

export function KnowledgeMastery({ courseName, knowledgePoints, onLearnClick, lang = 'zh', compact = false }: KnowledgeMasteryProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  // 按掌握度排序（从高到低）
  const sortedPoints = [...knowledgePoints].sort((a, b) => b.mastery - a.mastery)

  // 统一的主色渐变进度条
  const getProgressGradient = (mastery: number) => {
    if (mastery >= 80) return 'from-emerald-500 to-emerald-600'
    if (mastery >= 60) return 'from-blue-500 to-blue-600'
    if (mastery >= 40) return 'from-yellow-500 to-yellow-600'
    if (mastery >= 20) return 'from-orange-500 to-orange-600'
    return 'from-red-500 to-red-600'
  }

  return (
    <div className={`bg-card rounded-2xl border border-border p-6 h-full flex flex-col ${compact ? 'overflow-hidden' : ''}`}>
      <h3 className="font-semibold text-foreground flex items-center gap-2 mb-4 flex-shrink-0">
        <Brain className="w-5 h-5 text-primary" />
        {t('知识掌握度', 'Knowledge Mastery')}
        <span className="text-sm text-muted-foreground font-normal">- {courseName}</span>
      </h3>

      <div className="flex-1 overflow-auto">
        {sortedPoints.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground h-full flex flex-col items-center justify-center">
            <TrendingUp className="w-10 h-10 mb-2 opacity-50" />
            <p className="text-sm">{t('开始学习后查看知识掌握度', 'Start learning to see mastery')}</p>
            {onLearnClick && (
              <button type="button"
                onClick={() => onLearnClick()}
                className="mt-3 px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors"
              >
                {t('开始学习', 'Start Learning')}
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {sortedPoints.map((kp, index) => (
              <div key={index} className="group">
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="text-foreground font-medium">{kp.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">{kp.mastery}%</span>
                    {onLearnClick && kp.mastery < 80 && (
                      <button type="button"
                        onClick={() => onLearnClick(kp.courseId)}
                        className="text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity hover:underline flex items-center gap-0.5"
                      >
                        {t('去学习', 'Learn')}
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
                <div className="h-2.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 bg-gradient-to-r ${getProgressGradient(kp.mastery)}`}
                    style={{ width: `${kp.mastery}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部去学习按钮 */}
      {sortedPoints.length > 0 && onLearnClick && !compact && (
        <button type="button"
          onClick={() => onLearnClick()}
          className="mt-4 w-full py-2.5 bg-primary/10 text-primary rounded-xl font-medium hover:bg-primary/20 transition-colors"
        >
          {t('继续学习', 'Continue Learning')}
        </button>
      )}
    </div>
  )
}
