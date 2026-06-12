import type { Metadata } from 'next'
import SolutionsClient from './page-client'

export const metadata: Metadata = {
  title: '题解讨论 - 智码领航',
  description: '浏览、搜索和发布题解，与同学一起交流思路',
}

export default function Page() {
  return <SolutionsClient />
}
