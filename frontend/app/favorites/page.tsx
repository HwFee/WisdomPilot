import type { Metadata } from 'next'
import FavoritesClient from './page-client'

export const metadata: Metadata = {
  title: '收藏夹 - 智码领航',
  description: '管理你收藏的题目，按文件夹分类整理',
}

export default function Page() {
  return <FavoritesClient />
}
