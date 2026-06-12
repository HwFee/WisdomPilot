'use client'

import { useRouter } from 'next/navigation'
import { ArrowLeft, Star, CheckSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFavorites } from './hooks/use-favorites'
import { FavoriteCard } from './components/favorite-card'

export default function FavoritesClient() {
  const { back } = useRouter()
  const {
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
  } = useFavorites()

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
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => back()}
            aria-label="返回"
          >
            <ArrowLeft className="size-5" />
          </Button>
          <h1 className="text-lg font-semibold">收藏夹</h1>
          <span className="ml-auto text-sm text-muted-foreground">{favorites.length} 题</span>
          {favorites.length > 0 && (
            <Button
              type="button"
              variant={isSelectMode ? 'default' : 'ghost'}
              size="icon"
              onClick={() => {
                setSelectionState(prev => ({ ...prev, isSelectMode: !prev.isSelectMode, selectedIds: new Set() }))
              }}
              aria-label={isSelectMode ? '退出选择模式' : '进入选择模式'}
            >
              <CheckSquare className="size-5" />
            </Button>
          )}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pt-20 pb-8">
        {/* Folders */}
        {folders.length > 0 && (
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            <Button
              type="button"
              variant={selectedFolder === null ? 'default' : 'secondary'}
              size="sm"
              onClick={() => handleFolderChange(null)}
              className="whitespace-nowrap"
            >
              全部
            </Button>
            {folders.map(folder => (
              <Button
                type="button"
                key={folder.name}
                variant={selectedFolder === folder.name ? 'default' : 'secondary'}
                size="sm"
                onClick={() => handleFolderChange(folder.name)}
                className="whitespace-nowrap"
              >
                {folder.name} ({folder.count})
              </Button>
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
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleBatchDelete}
                className="text-red-500 hover:text-red-600"
              >
                删除
              </Button>
            </div>
          </div>
        )}

        {favorites.length === 0 ? (
          <div className="text-center py-16">
            <div className="size-16 rounded-full bg-yellow-500/10 flex items-center justify-center mx-auto mb-4">
              <Star className="size-8 text-yellow-500" />
            </div>
            <p className="text-muted-foreground">暂无收藏</p>
            <p className="text-sm text-muted-foreground mt-1">在练习中点击收藏按钮可以添加收藏</p>
          </div>
        ) : (
          <div className="flex flex-col gap-y-3">
            {favorites.map((fav) => (
              <FavoriteCard
                key={fav.id}
                fav={fav}
                isSelectMode={isSelectMode}
                isSelected={selectedIds.has(fav.id)}
                onToggleSelect={handleToggleSelect}
                onRemove={handleRemove}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
