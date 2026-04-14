'use client'

import { Suspense } from 'react'
import ChapterPageContent from './ChapterPageContent'

function ChapterPageFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-500">加载中...</p>
    </div>
  )
}

export default function ChapterPage() {
  return (
    <Suspense fallback={<ChapterPageFallback />}>
      <ChapterPageContent />
    </Suspense>
  )
}
