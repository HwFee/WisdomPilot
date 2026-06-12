'use client'

import { useRouter } from 'next/navigation'
import { Star, Trash2, CheckSquare, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { FavoriteResponse } from '@/types/api'
import { getTypeLabel, getSourceType, getSourceLabel, getQuestionTitle } from '../lib/favorite-utils'
import { ClientDate } from './client-date'

interface FavoriteCardProps {
  fav: FavoriteResponse
  isSelectMode: boolean
  isSelected: boolean
  onToggleSelect: (id: string) => void
  onRemove: (id: string) => void
}

export function FavoriteCard({ fav, isSelectMode, isSelected, onToggleSelect, onRemove }: FavoriteCardProps) {
  const { push } = useRouter()
  const sourceType = getSourceType(fav.exercise_key)
  const sourceLabel = getSourceLabel(fav.exercise_key)
  const questionTitle = getQuestionTitle(fav)

  // 从 exercise_key 提取 question_id 用于跳转
  // 格式: mastery-{courseId}-{chapterId}-{questionId} 或 arena-{courseId}-{questionId}
  const keyParts = fav.exercise_key?.split('-') || []
  let questionIdFromKey = ''

  if (sourceType === 'mastery' && keyParts.length >= 4) {
    questionIdFromKey = keyParts[3]
  } else if (sourceType === 'arena' && keyParts.length >= 3) {
    questionIdFromKey = keyParts[2]
  }

  const handleReview = async () => {
    const token = localStorage.getItem('token:v1')
    if (sourceType === 'arena' && token) {
      push('/arena')
    } else if (sourceType === 'mastery' && fav.course_id) {
      const chapterParam = fav.chapter_id || ''
      const questionParam = questionIdFromKey || ''
      const sectionParam = fav.section_id || ''
      push(`/mastery/${fav.course_id}?chapter=${chapterParam}&section=${sectionParam}&exercise=${questionParam}&skip=1`)
    } else if (fav.course_id) {
      push(`/mastery/${fav.course_id}`)
    }
  }

  return (
    <div
      className={`bg-card rounded-xl border border-border p-4 hover:border-primary/30 transition-all ${
        isSelected ? 'ring-2 ring-primary' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* 标题行 */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <Star className="size-4 text-yellow-500 flex-shrink-0 fill-yellow-500" />
            <span className="font-medium text-foreground truncate">{questionTitle}</span>
          </div>

          {/* 来源和状态标签 */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              sourceType === 'arena' ? 'bg-purple-500/10 text-purple-500' :
              'bg-blue-500/10 text-blue-500'
            }`}>
              {sourceLabel}
            </span>
            {fav.exercise_type && (
              <span className="text-xs px-2 py-0.5 bg-muted rounded-full">{getTypeLabel(fav.exercise_type)}</span>
            )}
            {fav.exercise_difficulty && (
              <span className="text-xs px-2 py-0.5 bg-muted rounded-full">难度 {fav.exercise_difficulty}</span>
            )}
            {fav.folder && (
              <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">{fav.folder}</span>
            )}
          </div>

          {/* 收藏时间 */}
          <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
            <span>收藏于 <ClientDate dateStr={fav.created_at} /></span>
          </div>

          {/* 知识点 */}
          {fav.knowledge_points && fav.knowledge_points.length > 0 && (
            <div className="flex gap-1 flex-wrap">
              {fav.knowledge_points.slice(0, 3).map((kp) => (
                <span key={kp} className="text-xs px-2 py-0.5 bg-primary/5 text-primary rounded-full">
                  {kp}
                </span>
              ))}
            </div>
          )}

          {/* 备注 */}
          {fav.note && (
            <p className="text-sm text-primary mt-2">{fav.note}</p>
          )}

          {/* 选择按钮 - 放在底部 */}
          {isSelectMode && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => onToggleSelect(fav.id)}
              className="mt-2"
              aria-label={isSelected ? '取消选择' : '选择'}
            >
              {isSelected ? (
                <CheckSquare className="size-5 text-primary" />
              ) : (
                <Square className="size-5 text-muted-foreground" />
              )}
            </Button>
          )}
        </div>

        <div className="flex flex-col items-end gap-2">
          {/* 复习按钮 */}
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleReview}
          >
            复习
          </Button>

          {/* 删除按钮 */}
          {!isSelectMode && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => onRemove(fav.id)}
              className="text-muted-foreground hover:text-red-500"
              aria-label="删除"
            >
              <Trash2 className="size-5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
