'use client'

import { useEffect, useState } from 'react'
import type { FavoriteResponse } from '@/types/api'

// 题目类型中文映射 - 完全参照错题本
export const TYPE_LABELS: Record<string, string> = {
  choice: '选择题',
  code: '编程题',
  programming: '编程题',
  fill: '填空题',
  fill_blank: '填空题',
  output: '输出题',
}

export function getTypeLabel(type?: string): string {
  if (!type) return '未知类型'
  return TYPE_LABELS[type] || type
}

// 从 exercise_key 推断来源类型 - 统一 mastery- 前缀
export function getSourceType(exerciseKey?: string): string {
  if (!exerciseKey) return 'unknown'
  if (exerciseKey.startsWith('mastery-')) return 'mastery'
  if (exerciseKey.startsWith('arena-')) return 'arena'
  return 'unknown'
}

// 来源类型中文映射
export const SOURCE_LABELS: Record<string, string> = {
  mastery: '精进之路',
  arena: '挑战之路',
  unknown: '未知来源',
}

export function getSourceLabel(exerciseKey?: string): string {
  const sourceType = getSourceType(exerciseKey)
  return SOURCE_LABELS[sourceType] || '未知来源'
}

export function ClientDate({ dateStr }: { dateStr: string }) {
  const [formatted, setFormatted] = useState('')
  useEffect(() => {
    setFormatted(new Date(dateStr).toLocaleDateString('zh-CN'))
  }, [dateStr])
  return <span>{formatted || dateStr.split('T')[0]}</span>
}

// 提取题目标题 - 与错题本一致
export function getQuestionTitle(fav: FavoriteResponse): string {
  // 优先从 exercise_content.text 提取
  if (fav.exercise_content?.text) {
    const text = fav.exercise_content.text
    return text.length > 50 ? text.substring(0, 50) + '...' : text
  }
  // 其次从 title 提取
  if (fav.exercise_content?.title) {
    return fav.exercise_content.title
  }
  // 最后用类型
  return getTypeLabel(fav.exercise_type)
}
