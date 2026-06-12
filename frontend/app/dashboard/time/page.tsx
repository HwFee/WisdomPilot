"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getStoredToken, logout, getTimeTrend } from "@/lib/api";
import { ArrowLeft, TrendingUp, TrendingDown, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Panel, PanelHeader, PageContainer } from "@/components/layout";
import type { DailyTimeTrendPoint } from "@/types/api";

function ClientDate({ date, options, className }: { date: string; options: Intl.DateTimeFormatOptions; className?: string }) {
  const formatted = new Date(date).toLocaleDateString('zh-CN', options)
  return <span className={className} suppressHydrationWarning>{formatted}</span>
}

export default function TimeDetailPage(){
  const { push, back } = useRouter();
  const [trends, setTrends] = useState<DailyTimeTrendPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const hasFetched = useRef(false);

  const fetchData = useCallback(async (token: string) => {
    try {
      const data = await getTimeTrend(token, 7);
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

  const todayMinutes = trends[0]?.minutes || 0;
  const yesterdayMinutes = trends[1]?.minutes || 0;
  const totalMinutes = trends.reduce((sum, t) => sum + t.minutes, 0);
  const avgMinutes =
    trends.length > 0 ? Math.round(totalMinutes / trends.length) : 0;
  const totalHours = Math.round((totalMinutes / 60) * 10) / 10;

  const trendPercent =
    yesterdayMinutes > 0
      ? Math.round(((todayMinutes - yesterdayMinutes) / yesterdayMinutes) * 100)
      : todayMinutes > 0
        ? 100
        : 0;

  // Calculate max for chart scaling
  const maxMinutes = Math.max(...trends.map((t) => t.minutes), 1);

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
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">学习时长趋势</h1>
        </div>
      </header>

      <main className="bg-background">
        <PageContainer className="py-12">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-px bg-border border border-border mb-6">
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">今日总时长</p>
              <p className="text-2xl font-bold text-foreground">
                {todayMinutes}分
              </p>
            </div>
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">
                7日总计（双路径）
              </p>
              <p className="text-2xl font-bold text-foreground">
                {totalHours}小时
              </p>
            </div>
            <div className="bg-card p-4">
              <p className="text-sm text-muted-foreground mb-1">日均总时长</p>
              <p className="text-2xl font-bold text-foreground">{avgMinutes}分</p>
            </div>
          </div>

          {/* Trend Panel */}
          <Panel className="mb-6">
            <PanelHeader
              title="学习时长趋势（精进之路 + 挑战之路）"
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
                          height: `${(t.minutes / maxMinutes) * 100}%`,
                          minHeight: t.minutes > 0 ? "4px" : "0",
                        }}
                      />
                      <ClientDate date={t.date} options={{ weekday: "short" }} className="text-xs text-muted-foreground" />
                    </div>
                  ))}
              </div>
            </div>
          </Panel>

          {/* Daily List */}
          <Panel>
            <PanelHeader title="每日详情（双路径总计）" />
            <div className="divide-y divide-border">
              {trends.map((t, i) => (
                <div key={t.date} className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`size-10 rounded-full flex items-center justify-center ${i === 0 ? "bg-foreground text-background" : "bg-muted text-muted-foreground"}`}
                    >
                      <Clock className="size-5" />
                    </div>
                    <div>
                      <p className="font-medium">
                        {i === 0 ? "今天" : i === 1 ? "昨天" : <ClientDate date={t.date} options={{ month: "short", day: "numeric" }} />}
                      </p>
                      <p className="text-sm text-muted-foreground">{t.date}</p>
                    </div>
                  </div>
                  <p className="text-xl font-bold text-foreground">
                    {t.minutes >= 60
                      ? `${Math.floor(t.minutes / 60)}小时${t.minutes % 60}分`
                      : `${t.minutes}分钟`}
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
