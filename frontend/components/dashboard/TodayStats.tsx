"use client";

import { Target, CheckCircle, Clock, Flame, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { StatsGrid, StatCell } from "@/components/layout";

interface TodayStatsProps {
  stats: {
    exercisesToday: number;
    accuracy: number;
    learningMinutes: number;
    streakDays?: number;
  };
  trend?: {
    exercises: number;
    accuracy: number;
    time?: number;
  };
  lang?: "zh" | "en";
  onExercisesClick?: () => void;
  onAccuracyClick?: () => void;
  onTimeClick?: () => void;
}

interface StatCardProps {
  icon: React.ReactNode;
  value: string | number;
  label: string;
  guide?: string;
  trend?: number;
  onClick?: () => void;
}

function StatCard({ icon, value, label, guide, trend, onClick }: StatCardProps) {
  return (
    <button
      type="button"
      className={cn(
        "flex flex-col justify-between h-full w-full text-left",
        !onClick && "cursor-default"
      )}
      onClick={onClick}
      disabled={!onClick}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="w-10 h-10 rounded-lg bg-secondary border border-border flex items-center justify-center">
          {icon}
        </div>

        {trend !== undefined && trend !== 0 && (
          <span
            className={cn(
              "flex items-center gap-1 text-xs font-medium",
              trend > 0 ? "text-emerald-600" : "text-red-600"
            )}
          >
            {trend > 0 ? (
              <TrendingUp className="w-3.5 h-3.5" strokeWidth={1.5} />
            ) : (
              <TrendingDown className="w-3.5 h-3.5" strokeWidth={1.5} />
            )}
            <span>{trend > 0 ? "+" : ""}{trend}%</span>
          </span>
        )}
      </div>

      <div className="flex-1 flex flex-col justify-end">
        <p className="text-3xl font-bold text-foreground tracking-tight font-[family-name:var(--font-display)]">
          {value}
        </p>
        <p className="text-sm text-muted-foreground mt-1">{label}</p>
        {guide && (
          <p className="text-xs text-primary mt-2 font-medium">
            {guide}
          </p>
        )}
      </div>
    </button>
  );
}

export function TodayStats({
  stats,
  trend,
  lang = "zh",
  onExercisesClick,
  onAccuracyClick,
  onTimeClick,
}: TodayStatsProps) {
  const t = (zh: string, en: string) => (lang === "zh" ? zh : en);

  const statCards = [
    {
      icon: <Target className="w-5 h-5 text-foreground" strokeWidth={1.5} />,
      value: stats.exercisesToday,
      label: t("今日做题（挑战之路）", "Exercises (Challenge Path)"),
      guide: stats.exercisesToday === 0 ? t("目标：10题 →", "Goal: 10") : undefined,
      trend: trend?.exercises,
      onClick: onExercisesClick,
    },
    {
      icon: <CheckCircle className="w-5 h-5 text-foreground" strokeWidth={1.5} />,
      value: `${stats.accuracy}%`,
      label: t("正确率（挑战之路）", "Accuracy (Challenge Path)"),
      guide: stats.accuracy === 0 ? t("保持专注 →", "Stay focused!") : undefined,
      trend: trend?.accuracy,
      onClick: onAccuracyClick,
    },
    {
      icon: <Clock className="w-5 h-5 text-foreground" strokeWidth={1.5} />,
      value: t(`${stats.learningMinutes}分钟`, `${stats.learningMinutes}min`),
      label: t("学习时长（双路径总计）", "Time (All Paths)"),
      guide: stats.learningMinutes === 0 ? t("目标：30分钟 →", "Goal: 30min") : undefined,
      trend: trend?.time,
      onClick: onTimeClick,
    },
    {
      icon: <Flame className="w-5 h-5 text-foreground" strokeWidth={1.5} />,
      value: stats.streakDays ?? 0,
      label: t("连续打卡", "Streak"),
      onClick: undefined,
    },
  ];

  return (
    <StatsGrid>
      {statCards.map((card) => (
        <StatCell key={card.label}>
          <StatCard {...card} />
        </StatCell>
      ))}
    </StatsGrid>
  );
}
