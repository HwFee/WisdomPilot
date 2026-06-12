"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getStoredToken, logout, getAccuracyTrend } from "@/lib/api";
import { ArrowLeft, TrendingUp, TrendingDown, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Panel, PanelHeader, PageContainer } from "@/components/layout";
import type { DailyAccuracyTrendPoint } from "@/types/api";

type EnrichedTrend = DailyAccuracyTrendPoint & { weekday: string; displayDate: string };

export default function AccuracyDetailPage() {
  const { push, back } = useRouter();
  const [trends, setTrends] = useState<EnrichedTrend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const hasFetched = useRef(false);

  const fetchData = useCallback(async (token: string) => {
    try {
      const data = await getAccuracyTrend(token, 7);
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
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回">
            <Link href="/dashboard"><ArrowLeft className="size-5" strokeWidth={1.5} /></Link>
          </Button>
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">正确率趋势</h1>
        </div>
      </header>

      <main className="bg-background">
        <PageContainer className="py-12">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-px bg-border border border-border mb-6">
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">
                今日正确率（挑战之路）
              </p>
              <p className="text-2xl font-bold text-foreground">
                {todayAccuracy}%
              </p>
            </div>
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">7日平均</p>
              <p className="text-2xl font-bold text-foreground">{avgAccuracy}%</p>
            </div>
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">总正确/总题</p>
              <p className="text-2xl font-bold text-foreground">
                {totalCorrect}/{totalAll}
              </p>
            </div>
          </div>

          {/* Trend Panel */}
          <Panel className="mb-6">
            <PanelHeader
              title="挑战之路正确率趋势"
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
              <div className="relative h-32 flex items-end justify-between gap-2">
                {trends
                  .slice()
                  .reverse()
                  .map((t) => (
                    <div
                      key={t.date}
                      className="flex-1 flex flex-col items-center gap-2"
                    >
                      <div
                        className="w-full rounded-t transition-all bg-primary"
                        style={{
                          height: `${t.accuracy}%`,
                          minHeight: t.accuracy > 0 ? "4px" : "0",
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
                      <CheckCircle className="size-5" />
                    </div>
                    <div>
                      <p className="font-medium">
                        {i === 0
                          ? "今天"
                          : i === 1
                            ? "昨天"
                            : t.displayDate}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {t.correct}/{t.total} 正确
                      </p>
                    </div>
                  </div>
                  <p className="text-xl font-bold text-foreground">
                    {t.accuracy}%
                  </p>
                </div>
              ))}
            </div>
          </Panel>
        </PageContainer>
      </main>
    </div>
  );
}
