'use client'

import { FileText } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { createNoteFromQuestion } from '@/lib/api/notes'
import type { NoteResponse } from '@/types/api'

const EMPTY_STRING_ARRAY: string[] = []

interface AiToNoteButtonProps {
  aiAnswerContent: string
  questionContent?: string
  exerciseId?: number
  chapterId?: number
  knowledgePoints?: string[]
  onCreated?: (note: NoteResponse) => void
  lang?: 'zh' | 'en'
}

export function AiToNoteButton({
  aiAnswerContent,
  questionContent,
  exerciseId,
  chapterId,
  knowledgePoints = EMPTY_STRING_ARRAY,
  onCreated,
  lang = 'zh',
}: AiToNoteButtonProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleCreateNote = async () => {
    const token = getStoredToken()
    if (!token) return

    try {
      const note = await createNoteFromQuestion(token, {
        title: t('AI回答笔记', 'AI Answer Note'),
        content: aiAnswerContent,
        exercise_id: exerciseId,
        chapter_id: chapterId,
        knowledge_points: knowledgePoints,
        source: 'ai_answer',
        question_content: questionContent,
        ai_answer_content: aiAnswerContent,
      })
      onCreated?.(note)
    } catch (error) {
      console.error('[笔记] 从AI回答创建失败:', error)
    }
  }

  return (
    <button type="button"
      onClick={handleCreateNote}
      className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors"
      title={t('将AI回答保存为笔记', 'Save AI answer as note')}
    >
      <FileText className="size-4" />
      {t('记为笔记', 'Save as Note')}
    </button>
  )
}
