'use client'

import { Lightbulb } from 'lucide-react'

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
}: ProblemPanelProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  return (
    <div className="h-full overflow-y-auto p-6 bg-card">
      <div className="max-w-2xl">
        {/* Title */}
        <h2 className="text-xl font-bold text-foreground mb-4">{title}</h2>

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
          <button
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
