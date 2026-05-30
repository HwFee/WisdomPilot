'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout, getFavorites, removeFavorite, getFavoriteFolders, updateFavorite, batchRemoveFavorites } from '@/lib/api'
import { ArrowLeft, Star, Trash2, CheckSquare, Square } from 'lucide-react'
import type { FavoriteResponse, FavoriteFolderResponse } from '@/types/api'

// 题目类型中文映射 - 完全参照错题本
const TYPE_LABELS: Record<string, string> = {
  choice: '选择题',
  code: '编程题',
  programming: '编程题',
  fill: '填空题',
  fill_blank: '填空题',
  output: '输出题',
}

function getTypeLabel(type?: string): string {
  if (!type) return '未知类型'
  return TYPE_LABELS[type] || type
}

// 从 exercise_key 推断来源类型 - 统一 mastery- 前缀
function getSourceType(exerciseKey?: string): string {
  if (!exerciseKey) return 'unknown'
  if (exerciseKey.startsWith('mastery-')) return 'mastery'
  if (exerciseKey.startsWith('arena-')) return 'arena'
  return 'unknown'
}

// 来源类型中文映射
const SOURCE_LABELS: Record<string, string> = {
  mastery: '精进之路',
  arena: '挑战之路',
  unknown: '未知来源',
}

function getSourceLabel(exerciseKey?: string): string {
  const sourceType = getSourceType(exerciseKey)
  return SOURCE_LABELS[sourceType] || '未知来源'
}

function ClientDate({ dateStr }: { dateStr: string }) {
  const [formatted, setFormatted] = useState('')
  useEffect(() => {
    setFormatted(new Date(dateStr).toLocaleDateString('zh-CN'))
  }, [dateStr])
  return <span>{formatted || dateStr.split('T')[0]}</span>
}

// 提取题目标题 - 与错题本一致
function getQuestionTitle(fav: FavoriteResponse): string {
  // 优先从 exercise_content.text 提取
  if (fav.exercise_content?.text) {
    const text = fav.exercise_content.text
    return text.length > 50 ? text.substring(0, 50) + '...' : text
  }
  // 其次从 title 提取
  if (fav.exercise_content?.title) {
    return fav.exercise_content.title
  }
  // 最后用类型
  return getTypeLabel(fav.exercise_type)
}

export default function FavoritesPage() {
  const { push, back } = useRouter()
  const [favorites, setFavorites] = useState<FavoriteResponse[]>([])
  const [folders, setFolders] = useState<FavoriteFolderResponse[]>([])
  const [selectionState, setSelectionState] = useState({
    selectedFolder: null as string | null,
    selectedIds: new Set<string>(),
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
  }, [push, back, fetchData])

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
          <button type="button"
            onClick={() => back()}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <ArrowLeft className="size-5" />
          </button>
          <h1 className="text-lg font-semibold">收藏夹</h1>
          <span className="ml-auto text-sm text-muted-foreground">{favorites.length} 题</span>
          {favorites.length > 0 && (
            <button type="button"
              onClick={() => {
                setSelectionState(prev => ({ ...prev, isSelectMode: !prev.isSelectMode, selectedIds: new Set() }))
              }}
              className={`p-2 rounded-lg transition-colors ${isSelectMode ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`}
            >
              <CheckSquare className="size-5" />
            </button>
          )}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pt-20 pb-8">
        {/* Folders */}
        {folders.length > 0 && (
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            <button type="button"
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
              <button type="button"
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
              <button type="button"
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
            <div className="size-16 rounded-full bg-yellow-500/10 flex items-center justify-center mx-auto mb-4">
              <Star className="size-8 text-yellow-500" />
            </div>
            <p className="text-muted-foreground">暂无收藏</p>
            <p className="text-sm text-muted-foreground mt-1">在练习中点击收藏按钮可以添加收藏</p>
          </div>
        ) : (
          <div className="flex flex-col gap-y-3">
            {favorites.map((fav) => {
              // 通过 exercise_key 推断来源类型 - 统一 mastery- 前缀
              const sourceType = getSourceType(fav.exercise_key)
              const sourceLabel = getSourceLabel(fav.exercise_key)
              const questionTitle = getQuestionTitle(fav)

              // 从 exercise_key 提取 question_id 用于跳转
              // 格式: mastery-{courseId}-{chapterId}-{questionId} 或 arena-{courseId}-{questionId}
              const keyParts = fav.exercise_key?.split('-') || []
              let questionIdFromKey = ''

              if (sourceType === 'mastery' && keyParts.length >= 4) {
                // mastery-{courseId}-{chapterId}-{questionId}
                questionIdFromKey = keyParts[3]
              } else if (sourceType === 'arena' && keyParts.length >= 3) {
                // arena-{courseId}-{questionId}
                questionIdFromKey = keyParts[2]
              }

              return (
                <div
                  key={fav.id}
                  className={`bg-card rounded-xl border border-border p-4 hover:border-primary/30 transition-all ${
                    selectedIds.has(fav.id) ? 'ring-2 ring-primary' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* 标题行 */}
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <Star className="size-4 text-yellow-500 flex-shrink-0 fill-yellow-500" />
                        <span className="font-medium text-foreground truncate">{questionTitle}</span>
                      </div>

                      {/* 来源和状态标签 */}
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          sourceType === 'arena' ? 'bg-purple-500/10 text-purple-500' :
                          'bg-blue-500/10 text-blue-500'
                        }`}>
                          {sourceLabel}
                        </span>
                        {fav.exercise_type && (
                          <span className="text-xs px-2 py-0.5 bg-muted rounded-full">{getTypeLabel(fav.exercise_type)}</span>
                        )}
                        {fav.exercise_difficulty && (
                          <span className="text-xs px-2 py-0.5 bg-muted rounded-full">难度 {fav.exercise_difficulty}</span>
                        )}
                        {fav.folder && (
                          <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">{fav.folder}</span>
                        )}
                      </div>

                      {/* 收藏时间 */}
                      <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                        <span>收藏于 <ClientDate dateStr={fav.created_at} /></span>
                      </div>

                      {/* 知识点 */}
                      {fav.knowledge_points && fav.knowledge_points.length > 0 && (
                        <div className="flex gap-1 flex-wrap">
                          {fav.knowledge_points.slice(0, 3).map((kp) => (
                            <span key={kp} className="text-xs px-2 py-0.5 bg-primary/5 text-primary rounded-full">
                              {kp}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* 备注 */}
                      {fav.note && (
                        <p className="text-sm text-primary mt-2">{fav.note}</p>
                      )}

                      {/* 选择按钮 - 放在底部 */}
                      {isSelectMode && (
                        <button type="button"
                          onClick={() => handleToggleSelect(fav.id)}
                          className="mt-2 p-1"
                        >
                          {selectedIds.has(fav.id) ? (
                            <CheckSquare className="size-5 text-primary" />
                          ) : (
                            <Square className="size-5 text-muted-foreground" />
                          )}
                        </button>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      {/* 复习按钮 */}
                      <button type="button"
                        onClick={async () => {
                          const token = localStorage.getItem('token:v1')
                          // 根据来源类型跳转到不同页面
                          if (sourceType === 'arena' && token) {
                            // 挑战之路: 直接跳转到挑战之路页面（独立于课程）
                            push('/arena')
                          } else if (sourceType === 'mastery' && fav.course_id) {
                            // 精进之路: 直接用收藏记录里的 chapter_id 和 section_id
                            const chapterParam = fav.chapter_id || ''
                            const questionParam = questionIdFromKey || ''
                            const sectionParam = fav.section_id || ''
                            push(`/mastery/${fav.course_id}?chapter=${chapterParam}&section=${sectionParam}&exercise=${questionParam}&skip=1`)
                          } else if (fav.course_id) {
                            push(`/mastery/${fav.course_id}`)
                          }
                        }}
                        className="px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-all flex-shrink-0"
                      >
                        复习
                      </button>

                      {/* 删除按钮 */}
                      {!isSelectMode && (
                        <button type="button"
                          onClick={() => handleRemove(fav.id)}
                          className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                        >
                          <Trash2 className="size-5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
