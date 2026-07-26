import type { Metadata } from 'next'
import { ArenaClient } from '@/components/arena/ArenaClient'

export const metadata: Metadata = {
  title: '调试竞技场 · 智码领航',
}

export default function ArenaPage() {
  return <ArenaClient />
}
