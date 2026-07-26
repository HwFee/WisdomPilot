import type { Metadata } from 'next'
import { Suspense } from 'react'
import { TutorClient } from '@/components/tutor/TutorClient'

export const metadata: Metadata = {
  title: '苏格拉底导师 · 智码领航',
}

export default function TutorPage() {
  return (
    <Suspense>
      <TutorClient />
    </Suspense>
  )
}
