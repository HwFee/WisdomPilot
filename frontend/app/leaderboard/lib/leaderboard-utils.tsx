import { Crown, Medal } from 'lucide-react'

const SUB_TIER_LABELS = ['I', 'II', 'III', 'IV', 'V'] as const

export function getRankIcon(rank: number) {
  switch (rank) {
    case 1:
      return <Crown className="size-6 text-amber-600" strokeWidth={1.5} />
    case 2:
      return <Medal className="size-6 text-muted-foreground" strokeWidth={1.5} />
    case 3:
      return <Medal className="size-6 text-amber-600" strokeWidth={1.5} />
    default:
      return <span className="text-lg font-bold text-muted-foreground">{rank}</span>
  }
}

export function getSubTierLabel(subTier: number): string {
  return SUB_TIER_LABELS[subTier - 1] ?? ''
}
