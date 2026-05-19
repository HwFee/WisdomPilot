"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Gem,
  TrendingUp,
  TrendingDown,
  History,
  RefreshCw,
  ArrowLeft,
  Calendar,
  Clock,
  Loader2,
} from "lucide-react";
import { getStoredToken } from "@/lib/api";
import {
  BEIJING_DAY_FORMATTER,
  BEIJING_TIME_FORMATTER,
  BEIJING_DATETIME_FORMATTER,
} from "@/lib/formatters";

interface CoreBalance {
  balance: number;
  total_earned: number;
  total_spent: number;
}

interface CoreTransaction {
  id: number;
  type: "earn" | "spend";
  category: string;
  amount: number;
  balance_after: number;
  reference_type?: string;
  reference_id?: string;
  description?: string;
  created_at: string;
}

interface TransactionListResponse {
  transactions: CoreTransaction[];
  total: number;
}

// 分类名称映射
const CATEGORY_NAMES: Record<string, string> = {
  // 获取
  mastery: "精进之路答题",
  arena: "挑战之路答题",
  checkin: "每日签到",
  study_time: "学习时长奖励",
  daily_exercises: "每日练习完成",
  daily_accuracy: "正确率奖励",
  bonus: "系统奖励",
  // 消耗
  ai_hint_light: "轻度提示",
  ai_hint_medium: "中度提示",
  ai_hint_deep: "深度解析",
};

// 分类颜色映射
const CATEGORY_COLORS: Record<string, string> = {
  mastery: "text-amber-600 bg-amber-50",
  arena: "text-blue-600 bg-blue-50",
  checkin: "text-green-600 bg-green-50",
  study_time: "text-cyan-600 bg-cyan-50",
  daily_exercises: "text-teal-600 bg-teal-50",
  daily_accuracy: "text-orange-600 bg-orange-50",
  bonus: "text-pink-600 bg-pink-50",
  ai_hint_light: "text-yellow-600 bg-yellow-50",
  ai_hint_medium: "text-purple-600 bg-purple-50",
  ai_hint_deep: "text-indigo-600 bg-indigo-50",
};

function CoreTransactionItem({ tx, formatDate, getCategoryColor, getCategoryName }: { tx: CoreTransaction; formatDate: (s: string) => string; getCategoryColor: (c: string) => string; getCategoryName: (c: string) => string }) {
  return (
    <div className="p-4 hover:bg-muted/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(tx.category)}`}>
              {getCategoryName(tx.category)}
            </span>
          </div>
          {tx.description && (
            <p className="text-sm text-muted-foreground truncate">{tx.description}</p>
          )}
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <Clock className="size-3" />
            {formatDate(tx.created_at)}
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className={`text-lg font-bold ${tx.type === "earn" ? "text-green-500" : "text-red-500"}`}>
            {tx.type === "earn" ? "+" : "-"}{tx.amount}
          </div>
          <div className="text-xs text-muted-foreground">余额: {tx.balance_after}</div>
        </div>
      </div>
    </div>
  );
}

export default function CoresPage() {
  const { push, back } = useRouter();
  const [balance, setBalance] = useState<CoreBalance | null>(null);
  const [transactions, setTransactions] = useState<CoreTransaction[]>([]);
  const pageRef = useRef(0);
  const [total, setTotal] = useState(0);
  const [loadingState, setLoadingState] = useState({ main: true, more: false })
  const { main: loading, more: loadingMore } = loadingState

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const PAGE_SIZE = 20;

  const fetchData = async (pageNum: number = 0, append: boolean = false) => {
    const token = getStoredToken();
    if (!token) {
      push("/login");
      return;
    }

    if (append) {
      setLoadingState(prev => ({ ...prev, more: true }))
    } else {
      setLoadingState(prev => ({ ...prev, main: true }))
    }

    try {
      // 获取余额
      const balanceRes = await fetch(`${API_URL}/api/cores/balance`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (balanceRes.ok) {
        setBalance(await balanceRes.json());
      }

      // 获取交易记录
      const transactionsRes = await fetch(
        `${API_URL}/api/cores/transactions?limit=${PAGE_SIZE}&offset=${pageNum * PAGE_SIZE}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (transactionsRes.ok) {
        const data: TransactionListResponse = await transactionsRes.json();
        if (append) {
          setTransactions((prev) => [...prev, ...data.transactions]);
        } else {
          setTransactions(data.transactions);
        }
        setTotal(data.total);
        pageRef.current = pageNum;
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoadingState({ main: false, more: false })
    }
  };

  useEffect(() => {
    fetchData(0);
  }, [push, back]);

  const loadMore = () => {
    if (!loadingState.more && transactions.length < total) {
      fetchData(pageRef.current + 1, true);
    }
  };

  const handleGoBack = () => {
    // 检查是否有历史记录可以返回
    if (window.history.length > 1 && document.referrer) {
      back()
    } else {
      // 如果没有历史记录，默认返回仪表盘
      push("/dashboard")
    }
  }

  const formatDate = (dateStr: string) => {
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

    // 获取北京时区的日期字符串用于比较
    const dateBeijingStr = BEIJING_DAY_FORMATTER.format(date)
    const nowBeijingStr = BEIJING_DAY_FORMATTER.format(now)

    // 计算时间差（毫秒）
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (dateBeijingStr === nowBeijingStr) {
      // 今天
      const hours = Math.floor(diff / (1000 * 60 * 60))
      if (hours === 0) {
        const minutes = Math.floor(diff / (1000 * 60))
        if (minutes < 1) return "刚刚"
        return `${minutes}分钟前`
      }
      return `${hours}小时前`
    } else if (days === 1 || (days === 0 && dateBeijingStr !== nowBeijingStr)) {
      // 昨天
      return "昨天 " + BEIJING_TIME_FORMATTER.format(date)
    } else if (days < 7) {
      return `${days}天前`
    } else {
      return BEIJING_DATETIME_FORMATTER.format(date)
    }
  };

  const getCategoryName = (category: string) => {
    return CATEGORY_NAMES[category] || category;
  };

  const getCategoryColor = (category: string) => {
    return CATEGORY_COLORS[category] || "text-gray-600 bg-gray-50";
  };

  // 统计数据 - 使用北京时区
  const todayTransactions = transactions.filter((t) => {
    // 后端返回的时间是 UTC，需要加上 Z 后缀才能正确解析
    let dateStr = t.created_at;
    if (!dateStr.endsWith('Z') && !dateStr.includes('+') && !dateStr.includes('T')) {
      dateStr = dateStr.replace(' ', 'T') + 'Z';
    } else if (dateStr.includes('T') && !dateStr.endsWith('Z') && !dateStr.includes('+')) {
      dateStr = dateStr + 'Z';
    }

    const date = new Date(dateStr);
    const today = new Date();

    // 比较北京时区的日期
    return BEIJING_DAY_FORMATTER.format(date) === BEIJING_DAY_FORMATTER.format(today);
  });

  const todayEarned = todayTransactions
    .filter((t) => t.type === "earn")
    .reduce((sum, t) => sum + t.amount, 0);

  const todaySpent = todayTransactions
    .filter((t) => t.type === "spend")
    .reduce((sum, t) => sum + t.amount, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="size-8 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white border-b">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <button type="button"
            onClick={handleGoBack}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-5" />
            <span className="font-medium">智核明细</span>
          </button>
          <button type="button"
            onClick={() => fetchData(0)}
            disabled={loading}
            className="p-2 text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className={`size-5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 gap-y-6">
        {/* Balance Card */}
        <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 rounded-2xl border border-purple-500/30 p-6">
          <div className="text-sm text-purple-400 mb-1">当前余额</div>
          <div className="text-4xl font-bold text-foreground flex items-center gap-3">
            <Gem className="size-8 text-purple-500" />
            {balance?.balance ?? 0}
          </div>
          <div className="flex gap-8 mt-4">
            <div>
              <div className="flex items-center gap-1 text-green-500 text-lg font-semibold">
                <TrendingUp className="size-4" />
                +{balance?.total_earned ?? 0}
              </div>
              <div className="text-xs text-muted-foreground">累计获得</div>
            </div>
            <div>
              <div className="flex items-center gap-1 text-red-500 text-lg font-semibold">
                <TrendingDown className="size-4" />
                -{balance?.total_spent ?? 0}
              </div>
              <div className="text-xs text-muted-foreground">累计消耗</div>
            </div>
          </div>
        </div>

        {/* Today Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-card rounded-xl border p-4">
            <div className="text-sm text-muted-foreground mb-1">今日获得</div>
            <div className="text-2xl font-bold text-green-500">+{todayEarned}</div>
          </div>
          <div className="bg-card rounded-xl border p-4">
            <div className="text-sm text-muted-foreground mb-1">今日消耗</div>
            <div className="text-2xl font-bold text-red-500">-{todaySpent}</div>
          </div>
        </div>

        {/* Transactions List */}
        <div className="bg-card rounded-xl border">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2">
              <History className="size-5 text-muted-foreground" />
              交易记录
            </h2>
            <span className="text-sm text-muted-foreground">共 {total} 条</span>
          </div>

          {transactions.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              暂无交易记录
            </div>
          ) : (
            <div className="divide-y">
              {transactions.map((tx) => (
                <CoreTransactionItem key={tx.id} tx={tx} formatDate={formatDate} getCategoryColor={getCategoryColor} getCategoryName={getCategoryName} />
              ))}

              {/* Load More Button */}
              {transactions.length < total && (
                <div className="p-4 text-center">
                  <button type="button"
                    onClick={loadMore}
                    disabled={loadingMore}
                    className="px-6 py-2 text-sm text-primary hover:bg-primary/10 rounded-lg disabled:opacity-50"
                  >
                    {loadingMore ? (
                      <Loader2 className="size-4 animate-spin inline mr-2" />
                    ) : null}
                    加载更多
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Help Text */}
        <div className="text-center text-xs text-muted-foreground pb-8">
          <p>智核可用于获取AI提示，帮助解题学习</p>
          <p className="mt-1">轻度提示(-1) · 中度提示(-3) · 深度解析(-5)</p>
        </div>
      </main>
    </div>
  );
}
