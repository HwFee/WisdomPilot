import type { Metadata } from 'next'
import CoursesClient from './page-client'

export const metadata: Metadata = {
  title: '选择课程 - 智码领航',
  description: '浏览并选择你要学习的程序设计课程',
}

export default function Page() {
  return <CoursesClient />
}
