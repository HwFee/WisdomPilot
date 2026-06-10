import type { SolutionSummary } from '@/lib/api/solutions'

export type CategoryType = 'hot' | 'new' | 'pinned' | 'announcement'
export type PageMode = 'list' | 'create'

export function filterSolutions(
  solutions: SolutionSummary[],
  query: string,
): SolutionSummary[] {
  const trimmed = query.trim().toLowerCase()
  if (!trimmed) return solutions

  const queryNum = parseInt(trimmed)

  return solutions.filter((s) => {
    if (queryNum && s.id === queryNum) return true
    return s.title.toLowerCase().includes(trimmed)
  })
}
