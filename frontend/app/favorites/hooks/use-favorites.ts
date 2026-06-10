'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout, getFavorites, removeFavorite, getFavoriteFolders, updateFavorite, batchRemoveFavorites } from '@/lib/api'
import type { FavoriteResponse, FavoriteFolderResponse } from '@/types/api'

interface SelectionState {
  selectedFolder: string | null
  selectedIds: Set<string>
  isSelectMode: boolean
}

export function useFavorites() {
  const { push } = useRouter()
  const [favorites, setFavorites] = useState<FavoriteResponse[]>([])
  const [folders, setFolders] = useState<FavoriteFolderResponse[]>([])
  const [selectionState, setSelectionState] = useState<SelectionState>({
    selectedFolder: null,
    selectedIds: new Set(),
    isSelectMode: false,
  })
  const { selectedFolder, selectedIds, isSelectMode } = selectionState
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
      push('/login')
      return
    }
    hasFetched.current = true
    fetchData(token)
  }, [push, fetchData])

  const handleFolderChange = async (folder: string | null) => {
    const token = getStoredToken()
    if (!token) return
    setSelectionState(prev => ({ ...prev, selectedFolder: folder, selectedIds: new Set() }))
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
    setSelectionState(prev => ({ ...prev, selectedIds: newSelected }))
  }

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return
    const token = getStoredToken()
    if (!token) return

    try {
      await batchRemoveFavorites(token, Array.from(selectedIds))
      setFavorites(prev => prev.filter(f => !selectedIds.has(f.id)))
      setSelectionState(prev => ({ ...prev, selectedIds: new Set(), isSelectMode: false }))
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
      fetchData(token, selectedFolder || undefined)
      setSelectionState(prev => ({ ...prev, selectedIds: new Set(), isSelectMode: false }))
    } catch {
      // Handle error silently
    }
  }

  return {
    favorites,
    folders,
    selectedFolder,
    selectedIds,
    isSelectMode,
    isLoading,
    setSelectionState,
    handleFolderChange,
    handleRemove,
    handleToggleSelect,
    handleBatchDelete,
    handleMoveToFolder,
  }
}
