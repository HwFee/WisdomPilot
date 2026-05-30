"use client";

import { Clock, Rocket, ArrowRight, CheckCircle, XCircle, Trophy, Flame, BookOpen, BookMarked, Pin, FileText, Book } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Activity {
  id: string;
  type?: string;
  activity_type?: string;
  description: string;
  created_at?: string;
  timestamp?: string;
  extra_data?: {
    stage_id?: number;
    stage_name?: string;
    exercise_id?: number;
    exercise_title?: string;
    exercises_completed?: number;
    exercises_correct?: number;
    is_correct?: boolean;
    learning_path?: "mastery" | "challenge" | string;
    learning_path_label?: string;
    // 精进之路/挑战之路共用字段
    section_id?: number;
    section_title?: string;
    chapter_title?: string;
    order_index?: number;
    difficulty?: number;
    exercise_index?: number;
  };
  // 兼容旧字段名
  details?: {
    stage_id?: number;
    stage_name?: string;
    exercise_id?: number;
    exercise_title?: string;
    exercises_completed?: number;
    exercises_correct?: number;
    is_correct?: boolean;
    learning_path?: "mastery" | "challenge" | string;
    learning_path_label?: string;
    section_id?: number;
    section_title?: string;
    chapter_title?: string;
    order_index?: number;
    difficulty?: number;
    exercise_index?: number;
  };
}

interface RecentActivityProps {
  activities: Activity[];
  onStartLearning?: () => void;
  lang?: "zh" | "en";
  compact?: boolean;
}

export function RecentActivity({
  activities,
  onStartLearning,
  lang = "zh",
  compact = false,
}: RecentActivityProps) {
  const t = (zh: string, en: string) => (lang === "zh" ? zh : en);

  const getLearningPathLabel = (activity: Activity) => {
    const data = activity.extra_data || activity.details;
    const explicitLabel = data?.learning_path_label;
    if (explicitLabel) return explicitLabel;

    const learningPath = data?.learning_path;
    if (learningPath === "mastery") {
      return t("精进之路", "Mastery");
    }
    if (learningPath === "challenge") {
      return t("挑战之路", "Challenge");
    }
    // 默认统一显示为练习题
    return t("练习题", "Exercise");
  };

  const getLearningPathBadgeClass = (activity: Activity) => {
    const learningPath = (activity.extra_data || activity.details)?.learning_path;
    if (learningPath === "mastery") {
      return "bg-amber-500/10 text-amber-600 dark:text-amber-400";
    }
    if (learningPath === "challenge") {
      return "bg-blue-500/10 text-blue-600 dark:text-blue-400";
    }
    // 默认统一练习题样式
    return "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400";
  };

  const getActivityIcon = (activity: Activity): LucideIcon => {
    const type = activity.type || activity.activity_type;
    if (!type) return Pin;

    if (type === "exercise_complete") {
      const data = activity.extra_data || activity.details;
      if (data?.is_correct === true) {
        return CheckCircle;
      } else if (data?.is_correct === false) {
        return XCircle;
      }
      return FileText;
    }

    switch (type) {
      case "chapter_complete":
      case "chapter_completed":
        return BookOpen;
      case "achievement_earned":
        return Trophy;
      case "streak":
        return Flame;
      case "chapter_started":
        return Book;
      default:
        return Pin;
    }
  };

  // 获取活动显示文本 - 对于练习完成，显示丰富信息
  const getActivityText = (activity: Activity) => {
    const type = activity.type || activity.activity_type;
    const data = activity.extra_data || activity.details;

    if (type === "exercise_complete" && data) {
      const learningPath = data.learning_path;

      // 精进之路：练习题X + 小节信息 + 正确/错误
      if (learningPath === "mastery") {
        const exerciseTitle = data.exercise_title || "练习题";
        // 组合章节和小节信息
        const sectionInfo = data.chapter_title || data.section_title
          ? `(${[data.chapter_title, data.section_title].filter(Boolean).join('-')})`
          : "";
        const isCorrect = data.is_correct;

        return (
          <>
            <span className="text-foreground">{exerciseTitle}{sectionInfo}</span>
            {isCorrect === true && <span className="text-emerald-500 ml-1">{t("正确", "Correct")}</span>}
            {isCorrect === false && <span className="text-red-500 ml-1">{t("错误", "Wrong")}</span>}
          </>
        );
      }

      // 挑战之路：难度X + 题目名称 + 正确/错误
      if (learningPath === "challenge") {
        const difficulty = data.difficulty;
        const exerciseTitle = data.exercise_title;
        const sectionInfo = data.section_title ? `(${data.section_title})` : "";
        const isCorrect = data.is_correct;

        return (
          <>
            <span className="text-foreground">
              {difficulty ? `难度 ${difficulty}` : "挑战题目"}
              {exerciseTitle && ` ${exerciseTitle}`}
              {sectionInfo}
            </span>
            {isCorrect === true && <span className="text-emerald-500 ml-1">{t("正确", "Correct")}</span>}
            {isCorrect === false && <span className="text-red-500 ml-1">{t("错误", "Wrong")}</span>}
          </>
        );
      }

      // 默认显示
      const exerciseName = data.exercise_title || data.stage_name || "练习";
      return (
        <>
          <span className="text-foreground">{exerciseName}</span>
          {data.is_correct === true && <span className="text-emerald-500 ml-1">✓</span>}
          {data.is_correct === false && <span className="text-red-500 ml-1">✗</span>}
        </>
      );
    }

    return activity.description;
  };

  // 格式化时间显示
  const formatTime = (timeStr?: string) => {
    if (!timeStr) return "";
    try {
      const date = new Date(timeStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return t("刚刚", "Just now");
      if (diffMins < 60) return t(`${diffMins} 分钟前`, `${diffMins} mins ago`);
      if (diffHours < 24)
        return t(`${diffHours} 小时前`, `${diffHours} hours ago`);
      if (diffDays < 7) return t(`${diffDays} 天前`, `${diffDays} days ago`);
      return date.toLocaleDateString();
    } catch {
      return timeStr;
    }
  };

  return (
    <div
      className={`bg-card rounded-2xl border border-border p-6 h-full flex flex-col ${compact ? "overflow-hidden" : ""}`}
    >
      <h3 className="font-semibold text-foreground flex items-center gap-2 mb-4 flex-shrink-0">
        <Clock className="size-5 text-primary" />
        {t("最近动态", "Recent Activity")}
      </h3>

      <div className="flex-1 overflow-auto max-h-[300px]">
        {activities.length === 0 ? (
          <div className="text-center py-6 h-full flex flex-col items-center justify-center">
            <Rocket className="size-10 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-sm text-muted-foreground mb-2">
              {t("暂无学习记录", "No activity yet")}
            </p>
            <p className="text-xs text-muted-foreground mb-4">
              {t("开始你的学习之旅吧！", "Start your learning journey!")}
            </p>
            {onStartLearning && (
              <button type="button"
                onClick={onStartLearning}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors"
              >
                {t("浏览课程", "Browse Courses")}
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-y-3">
            {activities.slice(0, compact ? 3 : 8).map((activity, index) => {
              const learningPathLabel = getLearningPathLabel(activity);

              return (
                <div
                  key={activity.id || index}
                  className="flex items-start gap-3 group"
                >
                  <div className="size-2 rounded-full bg-primary mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                      {learningPathLabel && (
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${getLearningPathBadgeClass(activity)}`}
                        >
                          {learningPathLabel}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-foreground line-clamp-2">
                      <span className="mr-1 inline-flex">
                        {(() => {
                          const Icon = getActivityIcon(activity);
                          return <Icon className="size-4" />;
                        })()}
                      </span>
                      {getActivityText(activity)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {formatTime(activity.created_at || activity.timestamp)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
