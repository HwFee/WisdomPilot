import type { Metadata } from 'next'
import { Suspense } from 'react'
import { CertificationClient } from '@/components/certification/CertificationClient'

export const metadata: Metadata = {
  title: '基本功认证 · 智码领航',
}

export default function CertificationPage() {
  return (
    <Suspense>
      <CertificationClient />
    </Suspense>
  )
}
