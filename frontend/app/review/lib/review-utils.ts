import type { WrongQuestionResponse as WrongQuestion } from '@/lib/api/review'

function getTypeLabel(type: string): string {
  switch (type) {
    case 'choice':
      return '选择题'
    case 'programming':
      return '编程题'
    case 'fill_blank':
      return '填空题'
    default:
      return type
  }
}

export function getQuestionTitle(wq: WrongQuestion): string {
  if (wq.question_title) return wq.question_title

  const titleFromContent = wq.exercise_content?.title
  if (typeof titleFromContent === 'string' && titleFromContent) {
    return titleFromContent
  }

  const textContent = wq.exercise_content?.text
  const textStr = typeof textContent === 'string' ? textContent : ''
  if (textStr) {
    return textStr.length > 60 ? textStr.substring(0, 60) + '...' : textStr
  }

  return getTypeLabel(wq.exercise_type)
}

export function getSourceInfo(wq: WrongQuestion): { type: string; label: string } {
  const type =
    wq.source_type || (wq.exercise_key?.startsWith('arena-') ? 'arena' : 'mastery')
  const label = wq.source_label || (type === 'arena' ? '挑战之路' : '精进之路')
  return { type, label }
}

export function getReviewUrl(wq: WrongQuestion): string {
  const { type: sourceType } = getSourceInfo(wq)
  const keyParts = wq.exercise_key?.split('-') || []
  let questionIdFromKey = ''

  if (sourceType === 'mastery' && keyParts.length >= 4) {
    questionIdFromKey = keyParts[3]
  } else if (sourceType === 'arena' && keyParts.length >= 3) {
    questionIdFromKey = keyParts[2]
  }

  if (sourceType === 'arena') {
    return '/arena'
  }

  if (sourceType === 'mastery' && wq.course_id) {
    const chapterParam = wq.chapter_id || ''
    const questionParam = questionIdFromKey || ''
    const sectionParam = wq.section_id || ''
    return `/mastery/${wq.course_id}?chapter=${chapterParam}&section=${sectionParam}&exercise=${questionParam}&skip=1`
  }

  if (wq.course_id) {
    return `/mastery/${wq.course_id}`
  }

  return '/dashboard'
}
