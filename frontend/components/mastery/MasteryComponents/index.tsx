'use client'

// Public re-exports for MasteryComponents.
// Only `MasteryProgressBar` is consumed by callers
// (see frontend/app/mastery/[courseId]/chapter/[chapterId]/page-client.tsx).
// `getMasteryLevel` lives in ./mastery-level and is intentionally not
// re-exported here — it has no external consumers, and the Rule 7
// pre-authorization lets us keep the public surface minimal.

export { MasteryProgressBar } from './ProgressBar'
