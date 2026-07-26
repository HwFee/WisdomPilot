import type { Metadata } from 'next'
import { AbilitiesClient } from '@/components/abilities/AbilitiesClient'

export const metadata: Metadata = {
  title: '能力图谱 · 智码领航',
}

export default function AbilitiesPage() {
  return <AbilitiesClient />
}
