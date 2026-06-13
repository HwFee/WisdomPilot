import type { Metadata } from 'next'
import LeaderboardClient from './page-client'

export const metadata: Metadata = {
  title: '排行榜 - 智码领航',
  description: '查看精进榜与竞技榜，与同学们一较高下',
}

export default function Page() {
  return <LeaderboardClient />
}
