'use client'

import Link from 'next/link'
import { Zap, ArrowLeft, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageContainer, EmptyState } from '@/components/layout'
import { TransactionList } from '@/components/transactions/transaction-list'
import { useXpData } from './hooks/use-xp-data'
import { XpStats } from './components/xp-stats'
import { XpTransactionItem } from './components/xp-transaction-item'

export default function XpClient() {
  const {
    balance,
    transactions,
    filter,
    filterOptions,
    isLoading,
    isLoadingMore,
    error,
    hasMore,
    setFilter,
    loadMore,
  } = useXpData()

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
          primaryAction={{ label: '刷新重试', href: '/xp' }}
        />
      </div>
    )
  }

  const hasNoData = !balance && transactions.length === 0
  const totalEarned = transactions.reduce((sum, t) => sum + t.amount, 0)
  const levelUpCount = transactions.filter((t) => t.level_up).length

  return (
    <div className="min-h-screen bg-background">
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回">
            <Link href="/dashboard">
              <ArrowLeft className="size-5" strokeWidth={1.5} />
            </Link>
          </Button>
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">经验流水</h1>
        </div>
      </header>

      <main className="bg-background">
        <PageContainer className="py-8 space-y-6">
          {hasNoData ? (
            <EmptyState
              icon={Zap}
              title="还没有经验流水"
              description="完成基础测试、精进测验或解锁成就后，这里会显示你的经验值明细。"
              primaryAction={{ label: '去学习中心', href: '/dashboard' }}
            />
          ) : (
            <>
              {balance && (
                <XpStats
                  balance={balance.balance}
                  level={balance.level}
                  totalEarned={totalEarned}
                  levelUpCount={levelUpCount}
                />
              )}

              <TransactionList
                title="经验明细"
                transactions={transactions}
                filter={filter}
                filterOptions={filterOptions}
                onFilterChange={(value) => setFilter(value as 'all' | 'earn')}
                hasMore={hasMore}
                onLoadMore={loadMore}
                isLoadingMore={isLoadingMore}
                emptyIcon={Zap}
                emptyTitle="暂无经验记录"
                emptyDescription="完成练习后，这里会显示经验值获取记录。"
                renderItem={(transaction) => (
                  <XpTransactionItem key={transaction.id} transaction={transaction} />
                )}
              />
            </>
          )}
        </PageContainer>
      </main>
    </div>
  )
}
