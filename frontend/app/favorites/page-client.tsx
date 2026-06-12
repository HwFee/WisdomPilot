'use client'

import Link from "next/link"
import { ArrowLeft, Star, CheckSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PageContainer, Panel, PanelHeader, EmptyState } from "@/components/layout"
import { useFavorites } from './hooks/use-favorites'
import { FavoriteCard } from './components/favorite-card'

export default function FavoritesClient() {
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
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回">
            <Link href="/dashboard">
              <ArrowLeft className="size-5" strokeWidth={1.5} />
            </Link>
          </Button>
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">我的收藏</h1>
          <div className="ml-auto flex items-center gap-2">
            {favorites.length > 0 && (
              <Button
                variant={isSelectMode ? 'default' : 'ghost'}
                onClick={() => {
                  setSelectionState((prev) => ({
                    ...prev,
                    isSelectMode: !prev.isSelectMode,
                    selectedIds: new Set(),
                  }))
                }}
              >
                {isSelectMode ? '退出选择' : '管理'}
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="bg-background min-h-[calc(100vh-3.5rem)]">
        <PageContainer className="py-8 space-y-6">
          {folders.length > 0 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              <Button
                variant={selectedFolder === null ? 'default' : 'secondary'}
                size="sm"
                onClick={() => handleFolderChange(null)}
                className="whitespace-nowrap"
              >
                全部
              </Button>
              {folders.map((folder) => (
                <Button
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

          {isSelectMode && selectedIds.size > 0 && (
            <Panel>
              <div className="px-6 py-3 flex items-center gap-3">
                <span className="text-sm text-muted-foreground">已选择 {selectedIds.size} 题</span>
                <div className="ml-auto flex gap-2">
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        handleMoveToFolder(e.target.value)
                        e.target.value = ''
                      }
                    }}
                    className="px-2 py-1 text-sm bg-background border border-border"
                  >
                    <option value="">移动到...</option>
                    <option value="重点题">重点题</option>
                    <option value="待复习">待复习</option>
                    <option value="易错题">易错题</option>
                  </select>
                  <Button variant="ghost" size="sm" onClick={handleBatchDelete} className="text-red-500 hover:text-red-600">
                    删除
                  </Button>
                </div>
              </div>
            </Panel>
          )}

          {favorites.length === 0 ? (
            <EmptyState
              icon={Star}
              title="还没有收藏"
              description="在题目页点击星标即可收藏。"
              primaryAction={{ label: '去 Arena 练习', href: '/arena' }}
            />
          ) : (
            <Panel>
              <PanelHeader title="收藏列表" count={`${favorites.length} 题`} />
              <div className="divide-y divide-border">
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
            </Panel>
          )}
        </PageContainer>
      </main>
    </div>
  )
}
