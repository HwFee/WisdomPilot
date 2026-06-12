'use client'

import { useRouter } from "next/navigation"
import { Star, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import type { FavoriteResponse } from "@/types/api"
import { getTypeLabel, getSourceType, getSourceLabel, getQuestionTitle } from "../lib/favorite-utils"
import { ClientDate } from "./client-date"

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
  const tags: string[] = []
  if (sourceLabel) tags.push(sourceLabel)
  if (fav.exercise_type) tags.push(getTypeLabel(fav.exercise_type))
  if (fav.folder) tags.push(fav.folder)

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
    <article className="px-6 py-4 flex items-center gap-4 hover:bg-muted/30">
      {isSelectMode && (
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onToggleSelect(fav.id)}
          aria-label="选择收藏"
          className="size-5"
        />
      )}
      {!isSelectMode && (
        <Star className="size-4 text-yellow-500 fill-yellow-500 flex-shrink-0" strokeWidth={1.5} />
      )}
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium truncate">{questionTitle}</h3>
        <p className="text-xs text-muted-foreground mt-1">
          {tags.join(' · ')} · 收藏于 <ClientDate dateStr={fav.created_at} />
        </p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <Button variant="secondary" size="sm" onClick={handleReview}>
          复习
        </Button>
        {!isSelectMode && (
          <Button variant="ghost" size="icon" onClick={() => onRemove(fav.id)} aria-label="删除">
            <Trash2 className="size-4 text-muted-foreground hover:text-red-500" strokeWidth={1.5} />
          </Button>
        )}
      </div>
    </article>
  )
}
