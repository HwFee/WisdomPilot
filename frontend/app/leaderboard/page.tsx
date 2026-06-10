'use client'

import { Suspense } from 'react'
import Link from 'next/link'
import { ArrowLeft, Trophy, Swords } from 'lucide-react'
import { useLeaderboard } from './hooks/use-leaderboard'
import { CurrentUserCard } from './components/current-user-card'
import { LeaderboardEntryItem } from './components/leaderboard-entry-item'

function LeaderboardContent() {
  const {
    activeTab, offset, loading,
    enrolledCourses, leaderboard,
    currentUserRank, currentUserData, currentUserId,
    limit,
    handleTabChange, handleLoadMore,
  } = useLeaderboard()



  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors group">
              <ArrowLeft className="size-4 group-hover:-translate-x-0.5 transition-transform" />
              <span className="text-sm">返回</span>
            </Link>
            <div className="flex items-center gap-2">
              {activeTab === 'mastery' ? (
                <>
                  <Trophy className="size-5 text-amber-500" />
                  <span className="font-semibold text-foreground">精进榜</span>
                </>
              ) : (
                <>
                  <Swords className="size-5 text-blue-500" />
                  <span className="font-semibold text-foreground">竞技榜</span>
                </>
              )}
            </div>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      <main className="pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Tabs */}
          <div className="mb-6">
            <div className="inline-flex items-center bg-muted rounded-xl p-1">
              <button type="button"
                onClick={() => handleTabChange('mastery')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'mastery'
                    ? 'bg-card text-amber-500 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Trophy className="size-4" />
                <span>精进榜</span>
              </button>
              <button type="button"
                onClick={() => handleTabChange('arena')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'arena'
                    ? 'bg-card text-blue-500 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Swords className="size-4" />
                <span>竞技榜</span>
              </button>
            </div>
          </div>

          {/* Current User Card */}
          {currentUserRank && (
            <CurrentUserCard
              activeTab={activeTab}
              currentUserRank={currentUserRank}
              currentUserData={currentUserData}
            />
          )}

          {/* No Data State */}
          {!loading && leaderboard.length === 0 && (
            <div className="text-center py-12">
              <div className={`size-16 rounded-full mx-auto mb-4 flex items-center justify-center ${
                activeTab === 'mastery' ? 'bg-amber-500/10' : 'bg-blue-500/10'
              }`}>
                {activeTab === 'mastery' ? (
                  <Trophy className="size-8 text-amber-500" />
                ) : (
                  <Swords className="size-8 text-blue-500" />
                )}
              </div>
              {enrolledCourses.length === 0 ? (
                <>
                  <p className="text-muted-foreground mb-2">你还没有选择任何课程</p>
                  <p className="text-sm text-muted-foreground">
                    先选择并加入一门课程后才能查看排行榜
                  </p>
                  <Link href="/dashboard" className="inline-block mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">
                    前往课程页面
                  </Link>
                </>
              ) : (
                <>
                  <p className="text-muted-foreground mb-2">暂无排名数据</p>
                  <p className="text-sm text-muted-foreground">
                    {activeTab === 'mastery'
                      ? '完成精进之路的学习和测试，获得经验值上榜'
                      : '参与竞技挑战，获得星星和段位上榜'}
                  </p>
                </>
              )}
            </div>
          )}

          {/* Leaderboard List */}
          {loading && offset === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent"></div>
            </div>
          ) : leaderboard.length > 0 && (
            <div className="flex flex-col gap-y-2">
              {leaderboard.map((entry) => (
                <LeaderboardEntryItem
                  key={entry.user_id}
                  entry={entry}
                  activeTab={activeTab}
                  isCurrentUser={entry.user_id === currentUserId}
                />
              ))}
            </div>
          )}

          {/* Load More */}
          {!loading && leaderboard.length >= limit && (
            <div className="text-center mt-6">
              <button type="button"
                onClick={handleLoadMore}
                className="px-6 py-2 bg-muted text-foreground rounded-xl text-sm font-medium hover:bg-muted/80 transition-colors"
              >
                加载更多
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Footer Info */}
      <div className="text-center pb-8">
        <p className="text-sm text-muted-foreground">
          {activeTab === 'mastery'
            ? '精进榜基于精进经验值计算排名，通过学习和答题获得经验'
            : '竞技榜按段位排名：大段位 > 小段位 > 星星数'}
        </p>
      </div>
    </div>
  )
}

export default function LeaderboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent"></div>
      </div>
    }>
      <LeaderboardContent />
    </Suspense>
  )
}
