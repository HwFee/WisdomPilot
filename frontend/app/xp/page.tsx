"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Zap,
  TrendingUp,
  History,
  RefreshCw,
  ArrowLeft,
  Clock,
  Loader2,
  Award,
  PartyPopper,
} from "lucide-react";
import { getStoredToken } from "@/lib/api";

interface XpBalance {
  balance: number;
  level: string;
}

interface XpTransaction {
  id: string;
  type: "earn" | "spend";
  category: string;
  amount: number;
  balance_after: number;
  level_before: string;
  level_after: string;
  level_up: boolean;
  reference_type?: string;
  reference_id?: string;
  description?: string;
  created_at: string;
}

interface TransactionListResponse {
  transactions: XpTransaction[];
  total: number;
}

// 分类名称映射
const CATEGORY_NAMES: Record<string, string> = {
  base_test: "基础测试答题",
  mastery_quiz: "精进测验完成",
  achievement: "成就奖励",
  bonus: "系统奖励",
};

// 分类颜色映射
const CATEGORY_COLORS: Record<string, string> = {
  base_test: "text-blue-600 bg-blue-50",
  mastery_quiz: "text-purple-600 bg-purple-50",
  achievement: "text-amber-600 bg-amber-50",
  bonus: "text-green-600 bg-green-50",
};

// 等级颜色映射
const LEVEL_COLORS: Record<string, string> = {
  入门: "text-gray-600 bg-gray-100",
  学习: "text-blue-600 bg-blue-100",
  练习: "text-green-600 bg-green-100",
  熟练: "text-purple-600 bg-purple-100",
  精通: "text-amber-600 bg-gradient-to-r from-amber-100 to-orange-100",
};

export default function XpPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [balance, setBalance] = useState<XpBalance | null>(null);
  const [transactions, setTransactions] = useState<XpTransaction[]>([]);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const PAGE_SIZE = 20;

  const fetchData = async (pageNum: number = 0, append: boolean = false) => {
    const token = getStoredToken();
    if (!token) {
      router.push("/login");
      return;
    }

    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      // 获取余额
      const balanceRes = await fetch(`${API_URL}/api/xp/balance`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (balanceRes.ok) {
        setBalance(await balanceRes.json());
      }

      // 获取交易记录
      const transactionsRes = await fetch(
        `${API_URL}/api/xp/transactions?limit=${PAGE_SIZE}&offset=${pageNum * PAGE_SIZE}`,
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
  }, [router]);

  const loadMore = () => {
    if (!loadingMore && transactions.length < total) {
      fetchData(page + 1, true);
    }
  };

  const handleGoBack = () => {
    if (window.history.length > 1 && document.referrer) {
      router.back();
    } else {
      router.push("/dashboard");
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

  const getCategoryName = (category: string) => {
    return CATEGORY_NAMES[category] || category;
  };

  const getCategoryColor = (category: string) => {
    return CATEGORY_COLORS[category] || "text-gray-600 bg-gray-50";
  };

  const getLevelColor = (level: string) => {
    return LEVEL_COLORS[level] || "text-gray-600 bg-gray-100";
  };

  // 统计数据 - 使用北京时区
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

  const todayEarned = todayTransactions
    .filter((t) => t.type === "earn")
    .reduce((sum, t) => sum + t.amount, 0);

  const todayLevelUps = todayTransactions.filter((t) => t.level_up).length;

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
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
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">经验明细</span>
          </button>
          <button type="button"
            onClick={() => fetchData(0)}
            disabled={loading}
            className="p-2 text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Balance Card */}
        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 rounded-2xl border border-blue-500/30 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Zap className="w-8 h-8 text-blue-500" />
            <div>
              <div className="text-sm text-blue-400 mb-1">精进之路经验</div>
              <div className="text-2xl font-bold text-foreground">
                {balance?.balance ?? 0} XP
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Award className="w-5 h-5 text-amber-500" />
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getLevelColor(balance?.level || "入门")}`}>
              {balance?.level || "入门"}
            </span>
          </div>
        </div>

        {/* Today Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-card rounded-xl border p-4">
            <div className="text-sm text-muted-foreground mb-1">今日获得</div>
            <div className="text-2xl font-bold text-green-500">+{todayEarned}</div>
          </div>
          <div className="bg-card rounded-xl border p-4">
            <div className="text-sm text-muted-foreground mb-1">今日升级</div>
            <div className="text-2xl font-bold text-amber-500">{todayLevelUps}</div>
          </div>
        </div>

        {/* Transactions List */}
        <div className="bg-card rounded-xl border">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2">
              <History className="w-5 h-5 text-muted-foreground" />
              经验记录
            </h2>
            <span className="text-sm text-muted-foreground">共 {total} 条</span>
          </div>

          {transactions.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              暂无经验记录
            </div>
          ) : (
            <div className="divide-y">
              {transactions.map((tx) => (
                <div key={tx.id} className="p-4 hover:bg-muted/30 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* 状态标签 */}
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        {tx.level_up && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium text-amber-600 bg-amber-100 flex items-center gap-1">
                            <PartyPopper className="w-3 h-3" />
                            升级
                          </span>
                        )}
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(tx.category)}`}>
                          {getCategoryName(tx.category)}
                        </span>
                      </div>

                      {/* 等级变化 */}
                      {tx.level_before !== tx.level_after && (
                        <div className="flex items-center gap-2 text-sm mb-1">
                          <span className={`px-2 py-0.5 rounded text-xs ${getLevelColor(tx.level_before)}`}>
                            {tx.level_before}
                          </span>
                          <span className="text-muted-foreground">→</span>
                          <span className={`px-2 py-0.5 rounded text-xs ${getLevelColor(tx.level_after)}`}>
                            {tx.level_after}
                          </span>
                        </div>
                      )}

                      {/* 描述 */}
                      {tx.description && (
                        <p className="text-sm text-muted-foreground truncate">
                          {tx.description}
                        </p>
                      )}

                      {/* 时间 */}
                      <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        {formatDate(tx.created_at)}
                      </div>
                    </div>

                    {/* 经验变化 */}
                    <div className="text-right flex-shrink-0">
                      <div className="text-lg font-bold text-green-500 flex items-center gap-1">
                        <TrendingUp className="w-4 h-4" />
                        +{tx.amount}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        累计: {tx.balance_after}
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
                      <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
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
          <p>精进之路答题正确获得经验值</p>
          <p className="mt-1">入门(0) → 学习(100) → 练习(300) → 熟练(600) → 精通(1000)</p>
        </div>
      </main>
    </div>
  );
}
