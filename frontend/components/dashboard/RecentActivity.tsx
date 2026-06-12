"use client";

import { Rocket } from "lucide-react";
import { cn } from "@/lib/utils";
import { Panel, PanelHeader, ActivityItem } from "@/components/layout";

// ============ 常量 ============
const MS_PER_MINUTE = 60000;
const MS_PER_HOUR = 3600000;
const MS_PER_DAY = 86400000;

const TIME_THRESHOLDS = {
  MINUTE: 1,
  HOUR: 60,
  DAY: 24,
  WEEK: 7,
} as const;

const ACTIVITY_DISPLAY_LIMITS = {
  compact: 3,
  full: 8,
} as const;

// ============ 类型 ============
interface Activity {
  id: string;
  type?: string;
  activity_type?: string;
  description: string;
  created_at?: string;
  timestamp?: string;
  extra_data?: {
    learning_path?: "mastery" | "challenge" | string;
    learning_path_label?: string;
  };
  details?: {
    learning_path?: "mastery" | "challenge" | string;
    learning_path_label?: string;
  };
}

interface RecentActivityProps {
  activities: Activity[];
  onStartLearning?: () => void;
  lang?: "zh" | "en";
  compact?: boolean;
}

// ============ 纯辅助函数 ============
const translate = (lang: "zh" | "en", zh: string, en: string) =>
  lang === "zh" ? zh : en;

const getLearningPathLabel = (activity: Activity, lang: "zh" | "en") => {
  const data = activity.extra_data || activity.details;
  if (data?.learning_path_label) return data.learning_path_label;

  const learningPath = data?.learning_path;
  if (learningPath === "mastery") {
    return translate(lang, "精进之路", "Mastery");
  }
  if (learningPath === "challenge") {
    return translate(lang, "挑战之路", "Challenge");
  }
  return translate(lang, "练习题", "Exercise");
};

const formatTime = (timeStr: string | undefined, lang: "zh" | "en") => {
  if (!timeStr) return "";
  try {
    const date = new Date(timeStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / MS_PER_MINUTE);
    const diffHours = Math.floor(diffMs / MS_PER_HOUR);
    const diffDays = Math.floor(diffMs / MS_PER_DAY);

    if (diffMins < TIME_THRESHOLDS.MINUTE)
      return translate(lang, "刚刚", "Just now");
    if (diffMins < TIME_THRESHOLDS.HOUR)
      return translate(lang, `${diffMins} 分钟前`, `${diffMins} mins ago`);
    if (diffHours < TIME_THRESHOLDS.DAY)
      return translate(lang, `${diffHours} 小时前`, `${diffHours} hours ago`);
    if (diffDays < TIME_THRESHOLDS.WEEK)
      return translate(lang, `${diffDays} 天前`, `${diffDays} days ago`);
    return date.toLocaleDateString();
  } catch {
    return timeStr;
  }
};

// ============ 组件 ============
export function RecentActivity({
  activities,
  onStartLearning,
  lang = "zh",
  compact = false,
}: RecentActivityProps) {
  const displayLimit = ACTIVITY_DISPLAY_LIMITS[compact ? "compact" : "full"];
  const t = (zh: string, en: string) => translate(lang, zh, en);

  return (
    <Panel className={cn("h-full flex flex-col", compact && "overflow-hidden")}>
      <PanelHeader title={t("最近活动", "Recent Activity")} />
      <div className="flex-1 overflow-auto">
        {activities.length === 0 ? (
          <div className="text-center px-8 py-10 h-full flex flex-col items-center justify-center">
            <Rocket
              className="size-10 mx-auto mb-3 text-muted-foreground opacity-50"
              strokeWidth={1.5}
            />
            <p className="text-sm text-muted-foreground mb-2">
              {t("暂无学习记录", "No activity yet")}
            </p>
            <p className="text-xs text-muted-foreground mb-4">
              {t("开始你的学习之旅吧！", "Start your learning journey!")}
            </p>
            {onStartLearning && (
              <button
                type="button"
                onClick={onStartLearning}
                className="px-4 py-2 bg-foreground text-background text-sm font-medium hover:bg-foreground/90 transition-colors"
              >
                {t("浏览课程", "Browse Courses")}
              </button>
            )}
          </div>
        ) : (
          <div>
            {activities.slice(0, displayLimit).map((activity) => {
              const learningPathLabel = getLearningPathLabel(activity, lang);
              return (
                <ActivityItem
                  key={activity.id}
                  time={formatTime(
                    activity.created_at || activity.timestamp,
                    lang
                  )}
                  title={activity.description}
                  meta={learningPathLabel}
                />
              );
            })}
          </div>
        )}
      </div>
    </Panel>
  );
}
