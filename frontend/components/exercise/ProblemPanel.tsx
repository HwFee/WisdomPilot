'use client'

import { Lightbulb } from 'lucide-react'
import { FavoriteButton } from './FavoriteButton'

interface ProblemPanelProps {
  title: string
  description: string
  inputFormat?: string
  outputFormat?: string
  sampleInput?: string
  sampleOutput?: string
  hints?: string[]
  knowledgePoints?: string[]
  onHintClick?: () => void
  lang?: 'zh' | 'en'
  // Favorite props - 与错题本一致
  exerciseKey?: string
  courseId?: number
  exerciseId?: number
  chapterId?: number
  exerciseContent?: {
    title?: string
    text?: string
    description?: string
    options?: string[]
  }
  exerciseType?: string
  exerciseDifficulty?: number
  showFavorite?: boolean
  onFavoriteChange?: (isFavorited: boolean) => void
}

export function ProblemPanel({
  title,
  description,
  inputFormat,
  outputFormat,
  sampleInput,
  sampleOutput,
  hints = [],
  knowledgePoints = [],
  onHintClick,
  lang = 'zh',
  // Favorite props
  exerciseKey,
  courseId,
  exerciseId,
  chapterId,
  exerciseContent,
  exerciseType,
  exerciseDifficulty,
  showFavorite = false,
  onFavoriteChange,
}: ProblemPanelProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  return (
    <div className="h-full overflow-y-auto p-6 bg-card">
      <div className="max-w-2xl">
        {/* Title with Favorite Button */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-foreground">{title}</h2>
          {showFavorite && exerciseKey && courseId && (
            <FavoriteButton
              exerciseKey={exerciseKey}
              courseId={courseId}
              exerciseId={exerciseId}
              chapterId={chapterId}
              exerciseContent={exerciseContent}
              exerciseType={exerciseType}
              exerciseDifficulty={exerciseDifficulty}
              knowledgePoints={knowledgePoints}
              size="md"
              showLabel
              lang={lang}
              onFavoriteChange={onFavoriteChange}
            />
          )}
        </div>

        {/* Description */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('题目描述', 'Description')}</h3>
          <p className="text-foreground leading-relaxed whitespace-pre-wrap">{description}</p>
        </div>

        {/* Input/Output Format */}
        {(inputFormat || outputFormat) && (
          <div className="mb-6 space-y-3">
            {inputFormat && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">{t('输入格式', 'Input')}</h3>
                <p className="text-foreground">{inputFormat}</p>
              </div>
            )}
            {outputFormat && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">{t('输出格式', 'Output')}</h3>
                <p className="text-foreground">{outputFormat}</p>
              </div>
            )}
          </div>
        )}

        {/* Sample Input/Output */}
        {(sampleInput || sampleOutput) && (
          <div className="mb-6 space-y-3">
            {sampleInput && (
              <div className="bg-muted/50 rounded-lg p-3">
                <h3 className="text-xs font-medium text-muted-foreground mb-1">{t('样例输入', 'Sample Input')}</h3>
                <pre className="text-sm font-mono text-foreground">{sampleInput}</pre>
              </div>
            )}
            {sampleOutput && (
              <div className="bg-muted/50 rounded-lg p-3">
                <h3 className="text-xs font-medium text-muted-foreground mb-1">{t('样例输出', 'Sample Output')}</h3>
                <pre className="text-sm font-mono text-foreground">{sampleOutput}</pre>
              </div>
            )}
          </div>
        )}

        {/* Knowledge Points */}
        {knowledgePoints.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('知识点', 'Knowledge Points')}</h3>
            <div className="flex flex-wrap gap-2">
              {knowledgePoints.map((point, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full"
                >
                  {point}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Hint Button */}
        {hints.length > 0 && onHintClick && (
          <button type="button"
            onClick={onHintClick}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-500/10 text-yellow-600 rounded-lg text-sm hover:bg-yellow-500/20 transition-colors"
          >
            <Lightbulb className="w-4 h-4" />
            {t('查看提示', 'Show Hint')} ({hints.length})
          </button>
        )}
      </div>
    </div>
  )
}
