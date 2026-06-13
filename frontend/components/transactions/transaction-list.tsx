'use client'

import { Loader2, type LucideIcon } from 'lucide-react'
import { Panel, PanelHeader, EmptyState } from '@/components/layout'
import { Button } from '@/components/ui/button'

export interface TransactionFilterOption {
  value: string
  label: string
}

interface TransactionListProps<T> {
  title: string
  transactions: T[]
  filter: string
  filterOptions: TransactionFilterOption[]
  onFilterChange: (filter: string) => void
  hasMore: boolean
  onLoadMore: () => void
  isLoadingMore: boolean
  emptyIcon: LucideIcon
  emptyTitle: string
  emptyDescription: string
  renderItem: (item: T) => React.ReactNode
  countLabel?: string
}

export function TransactionList<T>({
  title,
  transactions,
  filter,
  filterOptions,
  onFilterChange,
  hasMore,
  onLoadMore,
  isLoadingMore,
  emptyIcon,
  emptyTitle,
  emptyDescription,
  renderItem,
  countLabel = '笔',
}: TransactionListProps<T>) {
  return (
    <Panel>
      <PanelHeader
        title={title}
        count={`${transactions.length} ${countLabel}`}
        action={
          <div className="flex items-center gap-1">
            {filterOptions.map((option) => (
              <Button
                key={option.value}
                variant={filter === option.value ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onFilterChange(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        }
      />

      {transactions.length === 0 ? (
        <div className="px-6 py-16">
          <EmptyState icon={emptyIcon} title={emptyTitle} description={emptyDescription} />
        </div>
      ) : (
        <>
          <div className="divide-y divide-border">
            {transactions.map(renderItem)}
          </div>

          {hasMore && (
            <div className="p-4 border-t border-border flex justify-center">
              <Button variant="outline" onClick={onLoadMore} disabled={isLoadingMore}>
                {isLoadingMore && (
                  <Loader2 className="size-4 mr-2 animate-spin" strokeWidth={1.5} />
                )}
                加载更多
              </Button>
            </div>
          )}
        </>
      )}
    </Panel>
  )
}
