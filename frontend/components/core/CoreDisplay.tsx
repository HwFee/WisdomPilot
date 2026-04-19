'use client'

import { useEffect, useState } from 'react'
import { Gem, ChevronDown, History, TrendingUp, TrendingDown, X } from 'lucide-react'
import { getCoreBalance, getCoreTransactions, type CoreBalance, type CoreTransaction } from '@/lib/api/core'

interface CoreDisplayProps {
  initialBalance?: number
  showDetails?: boolean
  lang?: 'zh' | 'en'
}

export function CoreDisplay({ initialBalance = 0, showDetails = false, lang = 'zh' }: CoreDisplayProps) {
  const [balance, setBalance] = useState<CoreBalance>({
    balance: initialBalance,
    total_earned: 0,
    total_spent: 0,
  })
  const [isOpen, setIsOpen] = useState(false)
  const [transactions, setTransactions] = useState<CoreTransaction[]>([])
  const [loading, setLoading] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const data = await getCoreBalance()
        setBalance(data)
      } catch (error) {
        console.error('Failed to fetch core balance:', error)
      }
    }
    fetchBalance()
  }, [])

  const fetchTransactions = async () => {
    if (transactions.length > 0) return // Already loaded
    setLoading(true)
    try {
      const data = await getCoreTransactions(10, 0)
      setTransactions(data.transactions)
    } catch (error) {
      console.error('Failed to fetch transactions:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (dateStr: string) => {
    // 后端返回的时间是 UTC 时间，但可能没有时区后缀
    // 如果没有时区信息，加上 'Z' 表示 UTC
    let normalizedDateStr = dateStr;
    if (!dateStr.endsWith('Z') && !dateStr.includes('+') && !dateStr.includes('T')) {
      // 格式如 "2026-04-18 14:23:59"，转为 ISO 格式并加 Z
      normalizedDateStr = dateStr.replace(' ', 'T') + 'Z';
    } else if (dateStr.includes('T') && !dateStr.endsWith('Z') && !dateStr.includes('+')) {
      // 格式如 "2026-04-18T14:23:59"，加 Z
      normalizedDateStr = dateStr + 'Z';
    }

    const date = new Date(normalizedDateStr);
    const now = new Date();

    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return t('刚刚', 'Just now')
    if (diffMins < 60) return t(`${diffMins}分钟前`, `${diffMins}m ago`)
    if (diffHours < 24) return t(`${diffHours}小时前`, `${diffHours}h ago`)
    if (diffDays < 7) return t(`${diffDays}天前`, `${diffDays}d ago`)

    // 显示北京时区的日期
    return date.toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' })
  }

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      // Earn categories
      mastery: t('精进之路', 'Mastery'),
      arena: t('挑战之路', 'Arena'),
      checkin: t('每日签到', 'Check-in'),
      study_time: t('学习时长', 'Study Time'),
      daily_exercises: t('每日练习', 'Daily Exercises'),
      daily_accuracy: t('正确率奖励', 'Accuracy Bonus'),
      bonus: t('奖励', 'Bonus'),
      // Spend categories
      ai_hint_light: t('轻度提示', 'Light Hint'),
      ai_hint_medium: t('中度提示', 'Medium Hint'),
      ai_hint_deep: t('深度解析', 'Deep Analysis'),
    }
    return labels[category] || category
  }

  return (
    <div className="relative">
      {/* Core Balance Button */}
      <button
        onClick={() => {
          setIsOpen(!isOpen)
          if (!isOpen && showDetails) fetchTransactions()
        }}
        className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-500/10 hover:bg-purple-500/20 rounded-full transition-all"
      >
        <Gem className="w-4 h-4 text-purple-500" />
        <span className="text-sm font-medium text-purple-600 dark:text-purple-400">
          {balance.balance}
        </span>
        {showDetails && <ChevronDown className="w-3 h-3 text-purple-400" />}
      </button>

      {/* Dropdown Panel */}
      {isOpen && showDetails && (
        <div className="absolute right-0 mt-2 w-72 bg-card rounded-xl border border-border shadow-lg z-50">
          {/* Header */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-foreground">{t('智核', 'Cores')}</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-muted rounded-lg transition-colors"
              >
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <Gem className="w-6 h-6 text-purple-500" />
              <span className="text-2xl font-bold text-foreground">{balance.balance}</span>
            </div>
            <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-green-500" />
                <span>+{balance.total_earned}</span>
              </div>
              <div className="flex items-center gap-1">
                <TrendingDown className="w-3 h-3 text-red-500" />
                <span>-{balance.total_spent}</span>
              </div>
            </div>
          </div>

          {/* Recent Transactions */}
          <div className="p-3 max-h-64 overflow-y-auto">
            <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
              <History className="w-3 h-3" />
              {t('最近记录', 'Recent')}
            </div>

            {loading ? (
              <div className="py-4 text-center text-sm text-muted-foreground">
                {t('加载中...', 'Loading...')}
              </div>
            ) : transactions.length === 0 ? (
              <div className="py-4 text-center text-sm text-muted-foreground">
                {t('暂无记录', 'No records')}
              </div>
            ) : (
              <div className="space-y-2">
                {transactions.map((tx) => (
                  <div
                    key={tx.id}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-foreground truncate">
                        {getCategoryLabel(tx.category)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {formatTime(tx.created_at)}
                      </div>
                    </div>
                    <div className={`text-sm font-medium ${
                      tx.type === 'earn' ? 'text-green-500' : 'text-red-500'
                    }`}>
                      {tx.type === 'earn' ? '+' : '-'}{tx.amount}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-border">
            <a
              href="/cores"
              className="block text-center text-sm text-primary hover:text-primary-600 transition-colors"
            >
              {t('查看全部记录', 'View All Records')}
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

// Simple inline display for use in stats bars
export function CorePill({ balance }: { balance: number }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-500/10 rounded-full">
      <Gem className="w-4 h-4 text-purple-500" />
      <span className="text-sm font-medium text-purple-600 dark:text-purple-400">
        {balance}
      </span>
    </div>
  )
}
