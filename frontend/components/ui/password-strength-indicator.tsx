'use client'

import { cn } from '@/lib/utils'
import { Check, X } from 'lucide-react'

export type PasswordStrength = 'weak' | 'medium' | 'strong'

interface PasswordStrengthIndicatorProps {
  password: string
  strength?: PasswordStrength
  requirements?: {
    length: boolean
    letter: boolean
    digit: boolean
    special?: boolean
  }
  lang?: 'zh' | 'en'
}

const STRENGTH_CONFIG = {
  weak: { label: { zh: '弱', en: 'Weak' }, color: 'bg-red-500', width: '33%', textColor: 'text-red-500' },
  medium: { label: { zh: '中', en: 'Medium' }, color: 'bg-yellow-500', width: '66%', textColor: 'text-yellow-500' },
  strong: { label: { zh: '强', en: 'Strong' }, color: 'bg-green-500', width: '100%', textColor: 'text-green-500' },
}

export function PasswordStrengthIndicator({
  password,
  strength,
  requirements,
  lang = 'zh',
}: PasswordStrengthIndicatorProps) {
  if (!password) return null

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const strengthConfig = strength ? STRENGTH_CONFIG[strength] : null

  return (
    <div className="flex flex-col gap-y-2 mt-2">
      {/* Strength bar */}
      {strengthConfig && (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={cn('h-full rounded-full transition-all duration-300', strengthConfig.color)}
              style={{ width: strengthConfig.width }}
            />
          </div>
          <span className={cn('text-xs font-medium', strengthConfig.textColor)}>
            {strengthConfig.label[lang]}
          </span>
        </div>
      )}

      {/* Requirements checklist */}
      {requirements && (
        <div className="grid grid-cols-2 gap-1 text-xs">
          <RequirementItem
            met={requirements.length}
            text={t('至少8个字符', '8+ characters')}
          />
          <RequirementItem
            met={requirements.letter}
            text={t('包含字母', 'Contains letter')}
          />
          <RequirementItem
            met={requirements.digit}
            text={t('包含数字', 'Contains number')}
          />
          <RequirementItem
            met={requirements.special}
            text={t('特殊字符 (可选)', 'Special char (optional)')}
            optional
          />
        </div>
      )}
    </div>
  )
}

interface RequirementItemProps {
  met?: boolean
  text: string
  optional?: boolean
}

function RequirementItem({ met, text, optional }: RequirementItemProps) {
  return (
    <div className={cn(
      'flex items-center gap-1.5',
      met ? 'text-green-600 dark:text-green-400' : optional ? 'text-gray-400' : 'text-gray-500'
    )}>
      {met ? (
        <Check className="size-3 flex-shrink-0" />
      ) : (
        <X className={cn('size-3 flex-shrink-0', optional && 'opacity-50')} />
      )}
      <span className={cn(optional && !met && 'opacity-50')}>{text}</span>
    </div>
  )
}
