'use client'

import Link from 'next/link'
import { Gem, ArrowLeft, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageContainer, EmptyState } from '@/components/layout'
import { useCoreData } from './hooks/use-core-data'
import { CoreStats } from './components/core-stats'
import { CoreTransactionItem } from './components/core-transaction-item'
import { TransactionList } from '@/components/transactions/transaction-list'

export default function CoresClient() {
  const {
    balance,
    summary,
    transactions,
    filter,
    filterOptions,
    isLoading,
    isLoadingMore,
    error,
    hasMore,
    setFilter,
    loadMore,
  } = useCoreData()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-6">
        <EmptyState
          icon={RotateCcw}
          title="加载失败"
          description={error}
          primaryAction={{ label: '刷新重试', href: '/cores' }}
        />
      </div>
    )
  }

  const hasNoData = !balance && transactions.length === 0

  return (
    <div className="min-h-screen bg-background">
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回">
            <Link href="/dashboard">
              <ArrowLeft className="size-5" strokeWidth={1.5} />
            </Link>
          </Button>
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">智核流水</h1>
        </div>
      </header>

      <main className="bg-background">
        <PageContainer className="py-8 space-y-6">
          {hasNoData ? (
            <EmptyState
              icon={Gem}
              title="还没有智核流水"
              description="完成练习、签到或获取 AI 提示后，这里会显示你的智核余额与明细。"
              primaryAction={{ label: '去学习中心', href: '/dashboard' }}
            />
          ) : (
            <>
              {balance && summary && (
                <CoreStats
                  balance={balance.balance}
                  totalEarned={balance.total_earned}
                  totalSpent={balance.total_spent}
                  earnedToday={summary.earned_today}
                  spentToday={summary.spent_today}
                />
              )}

              <TransactionList
                title="流水明细"
                transactions={transactions}
                filter={filter}
                filterOptions={filterOptions}
                onFilterChange={(value) => setFilter(value as 'all' | 'earn' | 'spend')}
                hasMore={hasMore}
                onLoadMore={loadMore}
                isLoadingMore={isLoadingMore}
                emptyIcon={Gem}
                emptyTitle="暂无流水记录"
                emptyDescription="完成练习、签到或获取 AI 提示后，这里会显示明细。"
                renderItem={(transaction) => (
                  <CoreTransactionItem key={transaction.id} transaction={transaction} />
                )}
              />
            </>
          )}
        </PageContainer>
      </main>
    </div>
  )
}
