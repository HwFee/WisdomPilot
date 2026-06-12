import type { Metadata } from 'next'
import NotesClient from './page-client'

export const metadata: Metadata = {
  title: '我的笔记 - 智码领航',
  description: '记录学习心得，按标签筛选与导出',
}

export default function Page() {
  return <NotesClient />
}
