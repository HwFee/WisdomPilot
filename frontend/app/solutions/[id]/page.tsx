import type { Metadata } from 'next'
import SolutionDetailClient from './page-client'

export const metadata: Metadata = {
  title: '题解详情 - 智码领航',
  description: '查看题解的完整内容与讨论',
}

export default function Page() {
  return <SolutionDetailClient />
}