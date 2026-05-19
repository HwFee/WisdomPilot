"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getStoredToken, logout, getExercisesTrend } from "@/lib/api";
import { ArrowLeft, TrendingUp, TrendingDown, Target } from "lucide-react";
import type { DailyTrendPoint } from "@/types/api";

export default function ExercisesDetailPage() {
  const { push, back } = useRouter();
  const [trends, setTrends] = useState<DailyTrendPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const hasFetched = useRef(false);

  const fetchData = useCallback(async (token: string) => {
    try {
      const data = await getExercisesTrend(token, 7);
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

  const totalExercises = trends.reduce((sum, t) => sum + t.count, 0);
  const avgExercises =
    trends.length > 0 ? Math.round(totalExercises / trends.length) : 0;
  const todayCount = trends[0]?.count || 0;
  const yesterdayCount = trends[1]?.count || 0;
  const trendPercent =
    yesterdayCount > 0
      ? Math.round(((todayCount - yesterdayCount) / yesterdayCount) * 100)
      : todayCount > 0
        ? 100
        : 0;

  // Calculate max for chart scaling
  const maxCount = Math.max(...trends.map((t) => t.count), 1);

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
          <h1 className="text-lg font-semibold">今日做题详情（挑战之路）</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pt-20 pb-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="bg-card rounded-xl border border-border p-4">
            <p className="text-sm text-muted-foreground mb-1">
              今日做题（仅挑战之路）
            </p>
            <p className="text-2xl font-bold text-blue-500">{todayCount}</p>
          </div>
          <div className="bg-card rounded-xl border border-border p-4">
            <p className="text-sm text-muted-foreground mb-1">
              7日总计（挑战之路）
            </p>
            <p className="text-2xl font-bold text-foreground">
              {totalExercises}
            </p>
          </div>
          <div className="bg-card rounded-xl border border-border p-4">
            <p className="text-sm text-muted-foreground mb-1">
              日均（挑战之路）
            </p>
            <p className="text-2xl font-bold text-foreground">{avgExercises}</p>
          </div>
        </div>

        {/* Trend Card */}
        <div className="bg-card rounded-xl border border-border p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">挑战之路做题趋势</h2>
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

          {/* Simple Bar Chart */}
          <div className="flex items-end justify-between gap-2 h-32">
            {trends
              .slice()
              .reverse()
              .map((t, i) => (
                <div
                  key={`item-${i}`}
                  className="flex-1 flex flex-col items-center gap-2"
                >
                  <div
                    className="w-full bg-blue-500/80 rounded-t transition-all"
                    style={{
                      height: `${(t.count / maxCount) * 100}%`,
                      minHeight: t.count > 0 ? "4px" : "0",
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
              <div key={`item-${i}`} className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`size-10 rounded-full flex items-center justify-center ${i === 0 ? "bg-blue-500/10 text-blue-500" : "bg-muted text-muted-foreground"}`}
                  >
                    <Target className="size-5" />
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
                    <p className="text-sm text-muted-foreground">{t.date}</p>
                  </div>
                </div>
                <p className="text-xl font-bold">{t.count} 题</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
