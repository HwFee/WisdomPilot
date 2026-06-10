import { Crown, Medal } from 'lucide-react'

export function getRankIcon(rank: number) {
  switch (rank) {
    case 1:
      return <Crown className="size-6 text-yellow-500" />
    case 2:
      return <Medal className="size-6 text-gray-400" />
    case 3:
      return <Medal className="size-6 text-amber-600" />
    default:
      return <span className="text-lg font-bold text-muted-foreground">{rank}</span>
  }
}
