"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Crown,
  TrendingUp,
  TrendingDown,
  History,
  RefreshCw,
  ArrowLeft,
  Clock,
  Loader2,
  Shield,
  Star,
  PartyPopper,
} from "lucide-react";
import { getStoredToken } from "@/lib/api";

interface TierTransaction {
  id: string;
  course_id: number;
  tier_before: string;
  sub_tier_before: number;
  stars_before: number;
  tier_after: string;
  sub_tier_after: number;
  stars_after: number;
  stars_change: number;
  promoted: boolean;
  demoted: boolean;
  used_protection: boolean;
  protection_remaining: number;
  source: string;
  description: string | null;
  created_at: string;
}

interface TransactionListResponse {
  transactions: TierTransaction[];
  total: number;
}

// 段位名称映射
const TIER_NAMES: Record<string, string> = {
  bronze: "青铜",
  silver: "白银",
  gold: "黄金",
  platinum: "铂金",
  diamond: "钻石",
  master: "大师",
  grandmaster: "宗师",
  king: "王者",
};

const TIER_COLORS: Record<string, string> = {
  bronze: "text-amber-700 bg-amber-100",
  silver: "text-gray-600 bg-gray-200",
  gold: "text-yellow-600 bg-yellow-100",
  platinum: "text-cyan-600 bg-cyan-100",
  diamond: "text-blue-600 bg-blue-100",
  master: "text-purple-600 bg-purple-100",
  grandmaster: "text-red-600 bg-red-100",
  king: "text-orange-500 bg-gradient-to-r from-yellow-100 to-orange-100",
};

// 子段位罗马数字
const ROMAN_NUMERALS = ["", "I", "II", "III", "IV", "V"];

const getTierDisplay = (tier: string, subTier: number) => {
  return `${TIER_NAMES[tier] || tier} ${ROMAN_NUMERALS[subTier] || subTier}`;
};

export default function TierPage() {
  const { push, back } = useRouter();
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState<TierTransaction[]>([]);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const PAGE_SIZE = 20;

  const fetchData = async (pageNum: number = 0, append: boolean = false) => {
    const token = getStoredToken();
    if (!token) {
      push("/login");
      return;
    }

    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const res = await fetch(
        `${API_URL}/api/tier/transactions?limit=${PAGE_SIZE}&offset=${pageNum * PAGE_SIZE}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        const data: TransactionListResponse = await res.json();
        if (append) {
          setTransactions((prev) => [...prev, ...data.transactions]);
        } else {
          setTransactions(data.transactions);
        }
        setTotal(data.total);
        setPage(pageNum);
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchData(0);
  }, [push, back]);

  const loadMore = () => {
    if (!loadingMore && transactions.length < total) {
      fetchData(page + 1, true);
    }
  };

  const handleGoBack = () => {
    if (window.history.length > 1 && document.referrer) {
      back();
    } else {
      push("/dashboard");
    }
  };

  const formatDate = (dateStr: string) => {
    let normalizedDateStr = dateStr;
    if (!dateStr.endsWith("Z") && !dateStr.includes("+") && !dateStr.includes("T")) {
      normalizedDateStr = dateStr.replace(" ", "T") + "Z";
    } else if (dateStr.includes("T") && !dateStr.endsWith("Z") && !dateStr.includes("+")) {
      normalizedDateStr = dateStr + "Z";
    }

    const date = new Date(normalizedDateStr);
    const now = new Date();

    const beijingFormatter = (options: Intl.DateTimeFormatOptions) =>
      new Intl.DateTimeFormat("zh-CN", { ...options, timeZone: "Asia/Shanghai" });

    const dateBeijingStr = beijingFormatter({ year: "numeric", month: "numeric", day: "numeric" }).format(date);
    const nowBeijingStr = beijingFormatter({ year: "numeric", month: "numeric", day: "numeric" }).format(now);

    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (dateBeijingStr === nowBeijingStr) {
      const hours = Math.floor(diff / (1000 * 60 * 60));
      if (hours === 0) {
        const minutes = Math.floor(diff / (1000 * 60));
        if (minutes < 1) return "刚刚";
        return `${minutes}分钟前`;
      }
      return `${hours}小时前`;
    } else if (days === 1 || (days === 0 && dateBeijingStr !== nowBeijingStr)) {
      return "昨天 " + beijingFormatter({ hour: "2-digit", minute: "2-digit" }).format(date);
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return beijingFormatter({ month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(date);
    }
  };

  // 统计数据
  const todayTransactions = transactions.filter((t) => {
    let dateStr = t.created_at;
    if (!dateStr.endsWith("Z") && !dateStr.includes("+") && !dateStr.includes("T")) {
      dateStr = dateStr.replace(" ", "T") + "Z";
    } else if (dateStr.includes("T") && !dateStr.endsWith("Z") && !dateStr.includes("+")) {
      dateStr = dateStr + "Z";
    }

    const date = new Date(dateStr);
    const today = new Date();

    const beijingFormatter = new Intl.DateTimeFormat("zh-CN", {
      timeZone: "Asia/Shanghai",
      year: "numeric",
      month: "numeric",
      day: "numeric",
    });

    return beijingFormatter.format(date) === beijingFormatter.format(today);
  });

  const todayStarsGained = todayTransactions.filter((t) => t.stars_change > 0).reduce((sum, t) => sum + t.stars_change, 0);
  const todayStarsLost = todayTransactions.filter((t) => t.stars_change < 0).reduce((sum, t) => sum + Math.abs(t.stars_change), 0);
  const todayPromotions = todayTransactions.filter((t) => t.promoted).length;
  const todayDemotions = todayTransactions.filter((t) => t.demoted).length;

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
            <span className="font-medium">段位明细</span>
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
        {/* Header Card */}
        <div className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-2xl border border-amber-500/30 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Crown className="size-8 text-amber-500" />
            <div>
              <div className="text-sm text-amber-400 mb-1">段位变化记录</div>
              <div className="text-lg font-bold text-foreground">
                记录每次星星变化和段位升降
              </div>
            </div>
          </div>
        </div>

        {/* Today Summary */}
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-card rounded-xl border p-3 text-center">
            <div className="text-xl font-bold text-green-500">+{todayStarsGained}</div>
            <div className="text-xs text-muted-foreground">今日获得</div>
          </div>
          <div className="bg-card rounded-xl border p-3 text-center">
            <div className="text-xl font-bold text-red-500">-{todayStarsLost}</div>
            <div className="text-xs text-muted-foreground">今日失去</div>
          </div>
          <div className="bg-card rounded-xl border p-3 text-center">
            <div className="text-xl font-bold text-amber-500">{todayPromotions}</div>
            <div className="text-xs text-muted-foreground">今日晋级</div>
          </div>
          <div className="bg-card rounded-xl border p-3 text-center">
            <div className="text-xl font-bold text-gray-500">{todayDemotions}</div>
            <div className="text-xs text-muted-foreground">今日降级</div>
          </div>
        </div>

        {/* Transactions List */}
        <div className="bg-card rounded-xl border">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2">
              <History className="size-5 text-muted-foreground" />
              变化记录
            </h2>
            <span className="text-sm text-muted-foreground">共 {total} 条</span>
          </div>

          {transactions.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">暂无段位变化记录</div>
          ) : (
            <div className="divide-y">
              {transactions.map((tx) => (
                <div key={tx.id} className="p-4 hover:bg-muted/30 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* 状态标签 */}
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        {tx.promoted && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium text-green-600 bg-green-100 flex items-center gap-1">
                            <PartyPopper className="size-3" />
                            晋级
                          </span>
                        )}
                        {tx.demoted && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium text-red-600 bg-red-100 flex items-center gap-1">
                            <TrendingDown className="size-3" />
                            降级
                          </span>
                        )}
                        {tx.used_protection && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium text-blue-600 bg-blue-100 flex items-center gap-1">
                            <Shield className="size-3" />
                            段位保护
                          </span>
                        )}
                        {!tx.promoted && !tx.demoted && !tx.used_protection && (
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${TIER_COLORS[tx.tier_after] || "text-gray-600 bg-gray-100"}`}>
                            {getTierDisplay(tx.tier_after, tx.sub_tier_after)}
                          </span>
                        )}
                      </div>

                      {/* 段位变化 */}
                      <div className="flex items-center gap-2 text-sm">
                        <span className={`${TIER_COLORS[tx.tier_before] || "text-gray-600"} flex items-center gap-0.5`}>
                          {getTierDisplay(tx.tier_before, tx.sub_tier_before)} <Star className="size-3.5 fill-current" />{tx.stars_before}
                        </span>
                        <span className="text-muted-foreground">→</span>
                        <span className={`${TIER_COLORS[tx.tier_after] || "text-gray-600"} flex items-center gap-0.5`}>
                          {getTierDisplay(tx.tier_after, tx.sub_tier_after)} <Star className="size-3.5 fill-current" />{tx.stars_after}
                        </span>
                      </div>

                      {/* 描述 */}
                      {tx.description && (
                        <p className="text-sm text-muted-foreground mt-1">{tx.description}</p>
                      )}

                      {/* 时间 */}
                      <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                        <Clock className="size-3" />
                        {formatDate(tx.created_at)}
                      </div>
                    </div>

                    {/* 星星变化 */}
                    <div className="text-right flex-shrink-0">
                      <div
                        className={`text-lg font-bold flex items-center gap-1 ${
                          tx.stars_change > 0 ? "text-green-500" : "text-red-500"
                        }`}
                      >
                        {tx.stars_change > 0 ? (
                          <>
                            <TrendingUp className="size-4" />
                            +{tx.stars_change}
                          </>
                        ) : (
                          <>
                            <TrendingDown className="size-4" />
                            {tx.stars_change}
                          </>
                        )}
                        <Star className="size-4 fill-current" />
                      </div>
                    </div>
                  </div>
                </div>
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
          <p>挑战之路答题正确获得星星，错误失去星星</p>
          <p className="mt-1">积累足够星星可晋级，星星耗尽则降级</p>
        </div>
      </main>
    </div>
  );
}
