import type { Metadata } from 'next'
import MasteryChapterClient from './page-client'

export const metadata: Metadata = {
  title: '章节列表 - 智码领航',
  description: '浏览课程章节',
}

export default function Page() {
  return <MasteryChapterClient />
}