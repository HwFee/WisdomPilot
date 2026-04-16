'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout, getFavorites, removeFavorite, getFavoriteFolders, updateFavorite, batchRemoveFavorites } from '@/lib/api'
import { ArrowLeft, Star, Trash2, BookOpen, FolderOpen, MoreHorizontal, CheckSquare, Square } from 'lucide-react'
import type { FavoriteResponse, FavoriteFolderResponse } from '@/types/api'

export default function FavoritesPage() {
  const router = useRouter()
  const [favorites, setFavorites] = useState<FavoriteResponse[]>([])
  const [folders, setFolders] = useState<FavoriteFolderResponse[]>([])
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isSelectMode, setIsSelectMode] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const hasFetched = useRef(false)

  const fetchData = useCallback(async (token: string, folder?: string) => {
    try {
      const [favoritesData, foldersData] = await Promise.all([
        getFavorites(token, 100, 0, folder || undefined),
        getFavoriteFolders(token)
      ])
      setFavorites(favoritesData.favorites)
      setFolders(foldersData.folders)
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

  const handleFolderChange = async (folder: string | null) => {
    const token = getStoredToken()
    if (!token) return
    setSelectedFolder(folder)
    setSelectedIds(new Set())
    setIsLoading(true)
    try {
      const data = await getFavorites(token, 100, 0, folder || undefined)
      setFavorites(data.favorites)
    } catch {
      // Handle error silently
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemove = async (favoriteId: string) => {
    const token = getStoredToken()
    if (!token) return

    try {
      await removeFavorite(token, favoriteId)
      setFavorites(prev => prev.filter(f => f.id !== favoriteId))
      // Refresh folders
      const foldersData = await getFavoriteFolders(token)
      setFolders(foldersData.folders)
    } catch {
      // Handle error silently
    }
  }

  const handleToggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedIds.size === favorites.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(favorites.map(f => f.id)))
    }
  }

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return
    const token = getStoredToken()
    if (!token) return

    try {
      await batchRemoveFavorites(token, Array.from(selectedIds))
      setFavorites(prev => prev.filter(f => !selectedIds.has(f.id)))
      setSelectedIds(new Set())
      setIsSelectMode(false)
      // Refresh folders
      const foldersData = await getFavoriteFolders(token)
      setFolders(foldersData.folders)
    } catch {
      // Handle error silently
    }
  }

  const handleMoveToFolder = async (folder: string) => {
    if (selectedIds.size === 0) return
    const token = getStoredToken()
    if (!token) return

    try {
      await Promise.all(
        Array.from(selectedIds).map(id =>
          updateFavorite(token, id, { folder })
        )
      )
      // Refresh data
      fetchData(token, selectedFolder || undefined)
      setSelectedIds(new Set())
      setIsSelectMode(false)
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
          {favorites.length > 0 && (
            <button
              onClick={() => {
                setIsSelectMode(!isSelectMode)
                setSelectedIds(new Set())
              }}
              className={`p-2 rounded-lg transition-colors ${isSelectMode ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`}
            >
              <CheckSquare className="w-5 h-5" />
            </button>
          )}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pt-20 pb-8">
        {/* Folders */}
        {folders.length > 0 && (
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            <button
              onClick={() => handleFolderChange(null)}
              className={`px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors ${
                selectedFolder === null
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              }`}
            >
              全部
            </button>
            {folders.map(folder => (
              <button
                key={folder.name}
                onClick={() => handleFolderChange(folder.name)}
                className={`px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors ${
                  selectedFolder === folder.name
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                }`}
              >
                {folder.name} ({folder.count})
              </button>
            ))}
          </div>
        )}

        {/* Batch Actions */}
        {isSelectMode && selectedIds.size > 0 && (
          <div className="flex items-center gap-2 mb-4 p-2 bg-muted rounded-lg">
            <span className="text-sm text-muted-foreground">已选择 {selectedIds.size} 题</span>
            <div className="ml-auto flex gap-2">
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    handleMoveToFolder(e.target.value)
                    e.target.value = ''
                  }
                }}
                className="px-2 py-1 rounded text-sm bg-background border border-border"
              >
                <option value="">移动到...</option>
                <option value="重点题">重点题</option>
                <option value="待复习">待复习</option>
                <option value="易错题">易错题</option>
              </select>
              <button
                onClick={handleBatchDelete}
                className="px-2 py-1 rounded text-sm bg-red-500/10 text-red-500 hover:bg-red-500/20"
              >
                删除
              </button>
            </div>
          </div>
        )}

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
                className={`bg-card rounded-xl border border-border p-4 flex items-center justify-between ${
                  selectedIds.has(fav.id) ? 'ring-2 ring-primary' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  {isSelectMode && (
                    <button
                      onClick={() => handleToggleSelect(fav.id)}
                      className="p-1"
                    >
                      {selectedIds.has(fav.id) ? (
                        <CheckSquare className="w-5 h-5 text-primary" />
                      ) : (
                        <Square className="w-5 h-5 text-muted-foreground" />
                      )}
                    </button>
                  )}
                  <div className="w-10 h-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                    <Star className="w-5 h-5 text-yellow-500" />
                  </div>
                  <div>
                    <p className="font-medium">题目 #{fav.exercise_id}</p>
                    <p className="text-sm text-muted-foreground">
                      {fav.chapter_id
                        ? `章节 ${fav.chapter_id} - 小节 ${fav.subsection_index}`
                        : fav.challenge_session_id
                        ? '挑战之路'
                        : '未知来源'}
                    </p>
                    {fav.folder && (
                      <span className="inline-block px-2 py-0.5 bg-primary/10 text-primary text-xs rounded mt-1">
                        {fav.folder}
                      </span>
                    )}
                    {fav.note && (
                      <p className="text-sm text-primary mt-1">{fav.note}</p>
                    )}
                  </div>
                </div>
                {!isSelectMode && (
                  <button
                    onClick={() => handleRemove(fav.id)}
                    className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
