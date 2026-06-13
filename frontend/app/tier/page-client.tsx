'use client'

import Link from 'next/link'
import { Trophy, ArrowLeft, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageContainer, EmptyState } from '@/components/layout'
import { TransactionList } from '@/components/transactions/transaction-list'
import { useTierData } from './hooks/use-tier-data'
import { TierStats } from './components/tier-stats'
import { TierTransactionItem } from './components/tier-transaction-item'

export default function TierClient() {
  const {
    tierInfo,
    transactions,
    filter,
    filterOptions,
    isLoading,
    isLoadingMore,
    error,
    hasMore,
    setFilter,
    loadMore,
  } = useTierData()

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
          primaryAction={{ label: '刷新重试', href: '/tier' }}
        />
      </div>
    )
  }

  const hasNoData = !tierInfo && transactions.length === 0

  return (
    <div className="min-h-screen bg-background">
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回">
            <Link href="/dashboard">
              <ArrowLeft className="size-5" strokeWidth={1.5} />
            </Link>
          </Button>
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">段位流水</h1>
        </div>
      </header>

      <main className="bg-background">
        <PageContainer className="py-8 space-y-6">
          {hasNoData ? (
            <EmptyState
              icon={Trophy}
              title="还没有段位流水"
              description="参加挑战之路后，这里会显示段位升降与星星变化。"
              primaryAction={{ label: '去 Arena 挑战', href: '/arena' }}
            />
          ) : (
            <>
              {tierInfo && (
                <TierStats
                  tier={tierInfo.tier}
                  subTier={tierInfo.sub_tier}
                  stars={tierInfo.stars}
                  starsNeeded={tierInfo.stars_needed}
                  protectionRemaining={tierInfo.protection_remaining}
                  highestFullName={tierInfo.highest_full_name}
                />
              )}

              <TransactionList
                title="段位变化"
                transactions={transactions}
                filter={filter}
                filterOptions={filterOptions}
                onFilterChange={(value) => setFilter(value as 'all' | 'gain' | 'loss')}
                hasMore={hasMore}
                onLoadMore={loadMore}
                isLoadingMore={isLoadingMore}
                emptyIcon={Trophy}
                emptyTitle="暂无段位变化"
                emptyDescription="参加挑战后，这里会显示段位升降记录。"
                renderItem={(transaction) => (
                  <TierTransactionItem key={transaction.id} transaction={transaction} />
                )}
              />
            </>
          )}
        </PageContainer>
      </main>
    </div>
  )
}
