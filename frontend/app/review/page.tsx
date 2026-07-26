import type { Metadata } from 'next'
import { ReviewClient } from '@/components/review/ReviewClient'

export const metadata: Metadata = {
  title: '复盘 · 智码领航',
}

export default function ReviewPage() {
  return <ReviewClient />
}
