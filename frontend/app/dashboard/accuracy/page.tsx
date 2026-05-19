"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getStoredToken, logout, getAccuracyTrend } from "@/lib/api";
import { ArrowLeft, TrendingUp, TrendingDown, CheckCircle } from "lucide-react";
import type { DailyAccuracyTrendPoint } from "@/types/api";

export default function AccuracyDetailPage() {
  const { push, back } = useRouter();
  const [trends, setTrends] = useState<DailyAccuracyTrendPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const hasFetched = useRef(false);

  const fetchData = useCallback(async (token: string) => {
    try {
      const data = await getAccuracyTrend(token, 7);
      setTrends(data.trends);
    } catch {
      // Handle error silently
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasFetched.current) return;
    const token = getStoredToken();
    if (!token) {
      logout();
      push("/login");
      return;
    }
    hasFetched.current = true;
    fetchData(token);
  }, [push, back, fetchData]);

  const todayAccuracy = trends[0]?.accuracy || 0;
  const yesterdayAccuracy = trends[1]?.accuracy || 0;
  const totalCorrect = trends.reduce((sum, t) => sum + t.correct, 0);
  const totalAll = trends.reduce((sum, t) => sum + t.total, 0);
  // 计算总正确率（总正确数/总题数），而不是每日正确率的平均值
  const avgAccuracy = totalAll > 0 ? Math.round((totalCorrect / totalAll) * 100) : 0;

  const trendPercent =
    yesterdayAccuracy > 0
      ? Math.round((todayAccuracy - yesterdayAccuracy) * 10) / 10
      : 0;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center gap-3">
          <button type="button"
            onClick={() => back()}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <ArrowLeft className="size-5" />
          </button>
          <h1 className="text-lg font-semibold">正确率详情（挑战之路）</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pt-20 pb-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="bg-card rounded-xl border border-border p-4">
            <p className="text-sm text-muted-foreground mb-1">
              今日正确率（挑战之路）
            </p>
            <p className="text-2xl font-bold text-emerald-500">
              {todayAccuracy}%
            </p>
          </div>
          <div className="bg-card rounded-xl border border-border p-4">
            <p className="text-sm text-muted-foreground mb-1">7日平均</p>
            <p className="text-2xl font-bold text-foreground">{avgAccuracy}%</p>
          </div>
          <div className="bg-card rounded-xl border border-border p-4">
            <p className="text-sm text-muted-foreground mb-1">总正确/总题</p>
            <p className="text-2xl font-bold text-foreground">
              {totalCorrect}/{totalAll}
            </p>
          </div>
        </div>

        {/* Trend Card */}
        <div className="bg-card rounded-xl border border-border p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">挑战之路正确率趋势</h2>
            <div
              className={`flex items-center gap-1 text-sm ${trendPercent >= 0 ? "text-emerald-500" : "text-red-500"}`}
            >
              {trendPercent >= 0 ? (
                <TrendingUp className="size-4" />
              ) : (
                <TrendingDown className="size-4" />
              )}
              <span>
                {trendPercent >= 0 ? "+" : ""}
                {trendPercent}%
              </span>
            </div>
          </div>

          {/* Simple Line Chart using divs */}
          <div className="relative h-32 flex items-end justify-between gap-2">
            {trends
              .slice()
              .reverse()
              .map((t, i) => (
                <div
                  key={`accuracy-${i}`}
                  className="flex-1 flex flex-col items-center gap-2"
                >
                  <div
                    className="w-full rounded-t transition-all bg-emerald-500/80"
                    style={{
                      height: `${t.accuracy}%`,
                      minHeight: t.accuracy > 0 ? "4px" : "0",
                    }}
                  />
                  <span className="text-xs text-muted-foreground" suppressHydrationWarning>
                    {new Date(t.date).toLocaleDateString("zh-CN", {
                      weekday: "short",
                    })}
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Daily List */}
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="p-4 border-b border-border">
            <h2 className="font-semibold">每日详情（仅挑战之路）</h2>
          </div>
          <div className="divide-y divide-border">
            {trends.map((t, i) => (
              <div key={`accuracy-${i}`} className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`size-10 rounded-full flex items-center justify-center ${i === 0 ? "bg-emerald-500/10 text-emerald-500" : "bg-muted text-muted-foreground"}`}
                  >
                    <CheckCircle className="size-5" />
                  </div>
                  <div>
                    <p className="font-medium" suppressHydrationWarning>
                      {i === 0
                        ? "今天"
                        : i === 1
                          ? "昨天"
                          : new Date(t.date).toLocaleDateString("zh-CN", {
                              month: "short",
                              day: "numeric",
                            })}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {t.correct}/{t.total} 正确
                    </p>
                  </div>
                </div>
                <p
                  className={`text-xl font-bold ${t.accuracy >= 80 ? "text-emerald-500" : t.accuracy >= 60 ? "text-yellow-500" : "text-red-500"}`}
                >
                  {t.accuracy}%
                </p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
