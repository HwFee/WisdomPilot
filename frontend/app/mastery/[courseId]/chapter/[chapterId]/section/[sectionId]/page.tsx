import type { Metadata } from 'next'
import MasterySectionClient from './page-client'

export const metadata: Metadata = {
  title: '学习章节 - 智码领航',
  description: '章节内容与练习',
}

export default function Page() {
  return <MasterySectionClient />
}