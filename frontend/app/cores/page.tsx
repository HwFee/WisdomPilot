"use client";

import {
  Gem,
  TrendingUp,
  TrendingDown,
  History,
  RefreshCw,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import { CoreTransactionItem } from "./components/transaction-item";
import { useCoresData } from "./hooks/use-cores-data";
import { useTodayStats } from "./hooks/use-today-stats";

export const metadata = {
  title: "智核明细 - 智码领航",
  description: "查看智核交易记录",
};

export default function CoresPage() {
  const {
    balance,
    transactions,
    total,
    loadingState,
    fetchData,
    loadMore,
    back,
    push,
  } = useCoresData();

  const { todayEarned, todaySpent } = useTodayStats(transactions);

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

      <main className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-y-6">
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
                <CoreTransactionItem key={tx.id} tx={tx} />
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
