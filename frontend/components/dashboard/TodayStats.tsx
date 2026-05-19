"use client";

import { LazyMotion, domAnimation, m } from "framer-motion";
import {
  Target,
  CheckCircle,
  Clock,
  Flame,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { staggerContainer, staggerItem } from "@/lib/animations";

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
  color: string;
  gradient?: string;
  onClick?: () => void;
  delay?: number;
}

function StatCard({
  icon,
  value,
  label,
  guide,
  trend,
  color,
  gradient,
  onClick,
  delay = 0,
}: StatCardProps) {
  return (
    <m.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className={cn(
        "relative bg-card rounded-2xl border border-border p-5",
        "hover:shadow-xl hover:border-primary/30 transition-all duration-300",
        "min-h-[120px] flex flex-col overflow-hidden group",
        onClick && "cursor-pointer"
      )}
      onClick={onClick}
    >
      {/* 背景渐变装饰 */}
      {gradient && (
        <div className={cn(
          "absolute top-0 right-0 size-32 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500",
          gradient
        )} />
      )}

      <div className="relative z-10 flex items-center justify-between mb-3">
        <m.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3, delay: delay + 0.1 }}
          className={cn(
            "size-12 rounded-xl flex items-center justify-center shadow-sm",
            color
          )}
        >
          {icon}
        </m.div>

        {trend !== undefined && trend !== 0 && (
          <m.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: delay + 0.2 }}
            className={cn(
              "flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium",
              trend > 0
                ? "text-emerald-600 bg-emerald-500/10 border border-emerald-500/20"
                : "text-red-600 bg-red-500/10 border border-red-500/20"
            )}
          >
            {trend > 0 ? (
              <TrendingUp className="size-3.5" />
            ) : (
              <TrendingDown className="size-3.5" />
            )}
            <span>{trend > 0 ? "+" : ""}{trend}%</span>
          </m.div>
        )}
      </div>

      <div className="relative z-10 flex-1 flex flex-col justify-end">
        <m.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: delay + 0.15 }}
          className="text-3xl font-bold text-foreground tracking-tight"
        >
          {value}
        </m.p>
        <m.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: delay + 0.2 }}
          className="text-sm text-muted-foreground mt-1"
        >
          {label}
        </m.p>
        {guide && (
          <m.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: delay + 0.25 }}
            className="text-xs text-primary mt-2 hover:underline font-medium"
          >
            {guide}
          </m.p>
        )}
      </div>
    </m.div>
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
      icon: <Target className="size-5 text-blue-500" />,
      value: stats.exercisesToday,
      label: t("今日做题", "Exercises"),
      guide: stats.exercisesToday === 0 ? t("目标：10题 →", "Goal: 10") : undefined,
      trend: trend?.exercises,
      color: "bg-blue-500/10",
      gradient: "bg-blue-500/10",
      onClick: onExercisesClick,
    },
    {
      icon: <CheckCircle className="size-5 text-emerald-500" />,
      value: `${stats.accuracy}%`,
      label: t("正确率", "Accuracy"),
      guide: stats.accuracy === 0 ? t("保持专注 →", "Stay focused!") : undefined,
      trend: trend?.accuracy,
      color: "bg-emerald-500/10",
      gradient: "bg-emerald-500/10",
      onClick: onAccuracyClick,
    },
    {
      icon: <Clock className="size-5 text-purple-500" />,
      value: t(`${stats.learningMinutes}分钟`, `${stats.learningMinutes}min`),
      label: t("学习时长", "Time"),
      guide: stats.learningMinutes === 0 ? t("目标：30分钟 →", "Goal: 30min") : undefined,
      trend: trend?.time,
      color: "bg-purple-500/10",
      gradient: "bg-purple-500/10",
      onClick: onTimeClick,
    },
    {
      icon: <Flame className="size-5 text-orange-500" />,
      value: stats.streakDays ?? 0,
      label: t("连续打卡", "Streak"),
      color: "bg-orange-500/10",
      gradient: "bg-orange-500/10",
      onClick: undefined,
    },
  ];

  return (
    <LazyMotion features={domAnimation}>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {statCards.map((card, index) => (
          <StatCard
            key={card.label}
            {...card}
            delay={index * 0.1}
          />
        ))}
      </div>
    </LazyMotion>
  );
}
