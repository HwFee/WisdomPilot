'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout, getFavorites, removeFavorite } from '@/lib/api'
import { ArrowLeft, Star, Trash2, BookOpen } from 'lucide-react'
import type { FavoriteResponse } from '@/types/api'

export default function FavoritesPage() {
  const router = useRouter()
  const [favorites, setFavorites] = useState<FavoriteResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const hasFetched = useRef(false)

  const fetchData = useCallback(async (token: string) => {
    try {
      const data = await getFavorites(token)
      setFavorites(data.favorites)
    } catch {
      // Handle error silently
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    if (!token) {
      logout()
      router.push('/login')
      return
    }
    hasFetched.current = true
    fetchData(token)
  }, [router, fetchData])

  const handleRemove = async (favoriteId: string) => {
    const token = getStoredToken()
    if (!token) return

    try {
      await removeFavorite(token, favoriteId)
      setFavorites(prev => prev.filter(f => f.id !== favoriteId))
    } catch {
      // Handle error silently
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-semibold">收藏夹</h1>
          <span className="ml-auto text-sm text-muted-foreground">{favorites.length} 题</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pt-20 pb-8">
        {favorites.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 rounded-full bg-yellow-500/10 flex items-center justify-center mx-auto mb-4">
              <Star className="w-8 h-8 text-yellow-500" />
            </div>
            <p className="text-muted-foreground">暂无收藏</p>
            <p className="text-sm text-muted-foreground mt-1">在练习中点击收藏按钮可以添加收藏</p>
          </div>
        ) : (
          <div className="space-y-3">
            {favorites.map((fav) => (
              <div
                key={fav.id}
                className="bg-card rounded-xl border border-border p-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                    <Star className="w-5 h-5 text-yellow-500" />
                  </div>
                  <div>
                    <p className="font-medium">题目 #{fav.exercise_id}</p>
                    <p className="text-sm text-muted-foreground">
                      章节 {fav.chapter_id} - 小节 {fav.subsection_index}
                    </p>
                    {fav.note && (
                      <p className="text-sm text-primary mt-1">{fav.note}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleRemove(fav.id)}
                  className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
