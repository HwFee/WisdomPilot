import type { Metadata } from 'next'
import { DashboardClient } from '@/components/dashboard/DashboardClient'

export const metadata: Metadata = {
  title: '训练舱 · 智码领航',
}

export default function DashboardPage() {
  return <DashboardClient />
}
