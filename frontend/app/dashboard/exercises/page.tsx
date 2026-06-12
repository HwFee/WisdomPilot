"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getStoredToken, logout, getExercisesTrend } from "@/lib/api";
import { ArrowLeft, TrendingUp, TrendingDown, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Panel, PanelHeader, PageContainer } from "@/components/layout";
import type { DailyTrendPoint } from "@/types/api";

type EnrichedTrend = DailyTrendPoint & { weekday: string; displayDate: string };

export default function ExercisesDetailPage() {
  const { push, back } = useRouter();
  const [trends, setTrends] = useState<EnrichedTrend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const hasFetched = useRef(false);

  const fetchData = useCallback(async (token: string) => {
    try {
      const data = await getExercisesTrend(token, 7);
      const enriched = data.trends.map((t) => ({
        ...t,
        weekday: new Date(t.date).toLocaleDateString("zh-CN", { weekday: "short" }),
        displayDate: new Date(t.date).toLocaleDateString("zh-CN", { month: "short", day: "numeric" }),
      }));
      setTrends(enriched);
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
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回">
            <Link href="/dashboard"><ArrowLeft className="size-5" strokeWidth={1.5} /></Link>
          </Button>
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">今日做题趋势</h1>
        </div>
      </header>

      <main className="bg-background">
        <PageContainer className="py-12">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-px bg-border border border-border mb-6">
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">
                今日做题（仅挑战之路）
              </p>
              <p className="text-2xl font-bold text-foreground">{todayCount}</p>
            </div>
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">
                7日总计（挑战之路）
              </p>
              <p className="text-2xl font-bold text-foreground">
                {totalExercises}
              </p>
            </div>
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">
                日均（挑战之路）
              </p>
              <p className="text-2xl font-bold text-foreground">{avgExercises}</p>
            </div>
          </div>

          {/* Trend Panel */}
          <Panel className="mb-6">
            <PanelHeader
              title="挑战之路做题趋势"
              action={
                <div
                  className={`flex items-center gap-1 text-sm ${trendPercent >= 0 ? "text-foreground" : "text-muted-foreground"}`}
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
              }
            />
            <div className="p-8">
              <div className="flex items-end justify-between gap-2 h-32">
                {trends
                  .slice()
                  .reverse()
                  .map((t) => (
                    <div
                      key={t.date}
                      className="flex-1 flex flex-col items-center gap-2"
                    >
                      <div
                        className="w-full bg-primary rounded-t transition-all"
                        style={{
                          height: `${(t.count / maxCount) * 100}%`,
                          minHeight: t.count > 0 ? "4px" : "0",
                        }}
                      />
                      <span className="text-xs text-muted-foreground">
                        {t.weekday}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </Panel>

          {/* Daily List */}
          <Panel>
            <PanelHeader title="每日详情（仅挑战之路）" />
            <div className="divide-y divide-border">
              {trends.map((t, i) => (
                <div key={t.date} className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`size-10 rounded-full flex items-center justify-center ${i === 0 ? "bg-foreground text-background" : "bg-muted text-muted-foreground"}`}
                    >
                      <Target className="size-5" />
                    </div>
                    <div>
                      <p className="font-medium">
                        {i === 0
                          ? "今天"
                          : i === 1
                            ? "昨天"
                            : t.displayDate}
                      </p>
                      <p className="text-sm text-muted-foreground">{t.date}</p>
                    </div>
                  </div>
                  <p className="text-xl font-bold text-foreground">{t.count} 题</p>
                </div>
              ))}
            </div>
          </Panel>
        </PageContainer>
      </main>
    </div>
  );
}
