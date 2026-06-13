import type { Metadata } from 'next'
import HomeClient from './page-client'

export const metadata: Metadata = {
  title: '智码领航 - 基于生成式 AI 的程序设计实践教学系统',
  description: '智码领航 - 开启编程学习之旅',
}

export default function Page() {
  return <HomeClient />
}