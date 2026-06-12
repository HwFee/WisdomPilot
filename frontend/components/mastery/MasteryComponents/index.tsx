'use client'

// Public re-exports for MasteryComponents.
// Only `MasteryProgressBar` and `getMasteryLevel` are consumed by callers
// (see frontend/app/mastery/[courseId]/chapter/[chapterId]/page-client.tsx).
// The 4 card components (SectionMasteryCard, ChapterMasteryCard,
// CourseMasteryOverview, KnowledgePointMasteryCard) were verified unused
// via rg + git log -S and removed per AGENTS.md Rule 7.

export { MasteryProgressBar, getMasteryLevel } from './ProgressBar'