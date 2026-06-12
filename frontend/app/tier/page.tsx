"use client";

import {
  Crown,
  History,
  RefreshCw,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import { TierTransactionItem } from "./components/transaction-item";
import { useTierData } from "./hooks/use-tier-data";
import { useTierTodayStats } from "./hooks/use-tier-today-stats";

export const metadata = {
  title: "段位明细 - 智码领航",
  description: "查看段位变化记录",
};

export default function TierPage() {
  const {
    transactions,
    total,
    loading,
    loadingMore,
    fetchData,
    loadMore,
    back,
    push,
  } = useTierData();

  const {
    todayStarsGained,
    todayStarsLost,
    todayPromotions,
    todayDemotions,
  } = useTierTodayStats(transactions);

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

      <main className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-y-6">
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
                <TierTransactionItem key={tx.id} tx={tx} />
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
