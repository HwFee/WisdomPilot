"use client";

import {
  Zap,
  History,
  RefreshCw,
  ArrowLeft,
  Loader2,
  Award,
} from "lucide-react";
import { XpTransactionItem } from "./components/transaction-item";
import { useXpData } from "./hooks/use-xp-data";
import { useXpTodayStats } from "./hooks/use-xp-today-stats";
import { getLevelColor } from "./lib/xp-utils";

export default function XpPage() {
  const {
    balance,
    transactions,
    total,
    loadingState,
    fetchData,
    loadMore,
    back,
    push,
  } = useXpData();

  const { todayEarned, todayLevelUps } = useXpTodayStats(transactions);

  const { main: loading, more: loadingMore } = loadingState;

  const handleGoBack = () => {
    if (window.history.length > 1 && document.referrer) {
      back();
    } else {
      push("/dashboard");
    }
  };

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
            <span className="font-medium">经验明细</span>
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

      <main className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-y-6">
        {/* Balance Card */}
        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 rounded-2xl border border-blue-500/30 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Zap className="size-8 text-blue-500" />
            <div>
              <div className="text-sm text-blue-400 mb-1">精进之路经验</div>
              <div className="text-2xl font-bold text-foreground">
                {balance?.balance ?? 0} XP
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Award className="size-5 text-amber-500" />
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
              <History className="size-5 text-muted-foreground" />
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
                <XpTransactionItem key={tx.id} tx={tx} />
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
          <p>精进之路答题正确获得经验值</p>
          <p className="mt-1">入门(0) → 学习(100) → 练习(300) → 熟练(600) → 精通(1000)</p>
        </div>
      </main>
    </div>
  );
}
