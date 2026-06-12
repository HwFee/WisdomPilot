import type { Metadata } from 'next'
import ReviewClient from './page-client'

export const metadata: Metadata = {
  title: '错题本 - 智码领航',
  description: '回顾与复习历史错题，巩固薄弱知识点',
}

export default function Page() {
  return <ReviewClient />
}
