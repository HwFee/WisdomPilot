'use client'

// Public re-exports for MasteryComponents.
// Only `MasteryProgressBar` is currently consumed by callers (see
// frontend/app/mastery/[courseId]/chapter/[chapterId]/page-client.tsx).
// The card components are preserved per AGENTS.md Rule 7 (no autonomous
// deletion of dead code); they are exported below for potential future use.

export { MasteryProgressBar, getMasteryLevel } from './ProgressBar'
export { KnowledgePointMasteryCard } from './QuestionCard'
export { SectionMasteryCard, ChapterMasteryCard, CourseMasteryOverview } from './StatCell'
