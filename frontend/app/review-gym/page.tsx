import type { Metadata } from 'next'
import { Suspense } from 'react'
import { ReviewGymClient } from '@/components/review-gym/ReviewGymClient'

export const metadata: Metadata = {
  title: '代码审查室 · 智码领航',
}

export default function ReviewGymPage() {
  return (
    <Suspense>
      <ReviewGymClient />
    </Suspense>
  )
}
