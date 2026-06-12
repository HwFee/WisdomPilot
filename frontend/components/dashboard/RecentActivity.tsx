"use client";

import {
  Clock,
  Rocket,
  CheckCircle,
  XCircle,
  Trophy,
  Flame,
  BookOpen,
  Pin,
  FileText,
  Book,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

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

const MAX_HEIGHT_CLASS = "max-h-[300px]";
const BADGE_TEXT_CLASS = "text-[10px]";

// ============ 类型 ============
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
    section_id?: number;
    section_title?: string;
    chapter_title?: string;
    order_index?: number;
    difficulty?: number;
    exercise_index?: number;
  };
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

// ============ 纯辅助函数 ============
const translate = (lang: "zh" | "en", zh: string, en: string) =>
  lang === "zh" ? zh : en;

const getLearningPathLabel = (activity: Activity, lang: "zh" | "en") => {
  const data = activity.extra_data || activity.details;
  const explicitLabel = data?.learning_path_label;
  if (explicitLabel) return explicitLabel;

  const learningPath = data?.learning_path;
  if (learningPath === "mastery") {
    return translate(lang, "精进之路", "Mastery");
  }
  if (learningPath === "challenge") {
    return translate(lang, "挑战之路", "Challenge");
  }
  return translate(lang, "练习题", "Exercise");
};

const getLearningPathBadgeClass = (activity: Activity) => {
  const learningPath = (activity.extra_data || activity.details)?.learning_path;
  if (learningPath === "mastery") {
    return "bg-amber-500/10 text-amber-600 dark:text-amber-400";
  }
  if (learningPath === "challenge") {
    return "bg-blue-500/10 text-blue-600 dark:text-blue-400";
  }
  return "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400";
};

const getActivityIcon = (activity: Activity): LucideIcon => {
  const type = activity.type || activity.activity_type;
  if (!type) return Pin;

  if (type === "exercise_complete") {
    const data = activity.extra_data || activity.details;
    if (data?.is_correct === true) {
      return CheckCircle;
    }
    if (data?.is_correct === false) {
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

const getMasteryActivityText = (
  data: Activity["extra_data"],
  lang: "zh" | "en"
) => {
  const exerciseTitle = data?.exercise_title || "练习题";
  const sectionInfo =
    data?.chapter_title || data?.section_title
      ? `(${[data.chapter_title, data.section_title].filter(Boolean).join("-")})`
      : "";
  const isCorrect = data?.is_correct;

  return (
    <>
      <span className="text-foreground">
        {exerciseTitle}
        {sectionInfo}
      </span>
      <CorrectnessLabel isCorrect={isCorrect} lang={lang} />
    </>
  );
};

const getChallengeActivityText = (
  data: Activity["extra_data"],
  lang: "zh" | "en"
) => {
  const difficulty = data?.difficulty;
  const exerciseTitle = data?.exercise_title;
  const sectionInfo = data?.section_title ? `(${data.section_title})` : "";
  const isCorrect = data?.is_correct;

  return (
    <>
      <span className="text-foreground">
        {difficulty ? `难度 ${difficulty}` : "挑战题目"}
        {exerciseTitle && ` ${exerciseTitle}`}
        {sectionInfo}
      </span>
      <CorrectnessLabel isCorrect={isCorrect} lang={lang} />
    </>
  );
};

const CorrectnessLabel = ({
  isCorrect,
  lang,
}: {
  isCorrect: boolean | undefined;
  lang: "zh" | "en";
}) => {
  if (isCorrect === true) {
    return (
      <span className="text-emerald-500 ml-1">
        {translate(lang, "正确", "Correct")}
      </span>
    );
  }
  if (isCorrect === false) {
    return (
      <span className="text-red-500 ml-1">
        {translate(lang, "错误", "Wrong")}
      </span>
    );
  }
  return null;
};

const getDefaultActivityText = (
  data: Activity["extra_data"],
  _lang: "zh" | "en"
) => {
  const exerciseName = data?.exercise_title || data?.stage_name || "练习";
  return (
    <>
      <span className="text-foreground">{exerciseName}</span>
      {data?.is_correct === true && (
        <CheckCircle
          className="size-4 inline text-emerald-500 ml-1"
          strokeWidth={1.5}
        />
      )}
      {data?.is_correct === false && (
        <XCircle
          className="size-4 inline text-red-500 ml-1"
          strokeWidth={1.5}
        />
      )}
    </>
  );
};

const getActivityText = (activity: Activity, lang: "zh" | "en") => {
  const type = activity.type || activity.activity_type;
  const data = activity.extra_data || activity.details;

  if (type === "exercise_complete" && data) {
    const learningPath = data.learning_path;

    if (learningPath === "mastery") {
      return getMasteryActivityText(data, lang);
    }

    if (learningPath === "challenge") {
      return getChallengeActivityText(data, lang);
    }

    return getDefaultActivityText(data, lang);
  }

  return activity.description;
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

  return (
    <div
      className={`bg-card rounded-lg border border-border p-6 h-full flex flex-col ${compact ? "overflow-hidden" : ""}`}
    >
      <h3 className="font-semibold text-foreground flex items-center gap-2 mb-4 flex-shrink-0">
        <Clock className="size-5 text-primary" strokeWidth={1.5} />
        {translate(lang, "最近动态", "Recent Activity")}
      </h3>

      <div className={`flex-1 overflow-auto ${MAX_HEIGHT_CLASS}`}>
        {activities.length === 0 ? (
          <div className="text-center py-6 h-full flex flex-col items-center justify-center">
            <Rocket
              className="size-10 mx-auto mb-3 text-muted-foreground opacity-50"
              strokeWidth={1.5}
            />
            <p className="text-sm text-muted-foreground mb-2">
              {translate(lang, "暂无学习记录", "No activity yet")}
            </p>
            <p className="text-xs text-muted-foreground mb-4">
              {translate(lang, "开始你的学习之旅吧！", "Start your learning journey!")}
            </p>
            {onStartLearning && (
              <button
                type="button"
                onClick={onStartLearning}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors"
              >
                {translate(lang, "浏览课程", "Browse Courses")}
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-y-3">
            {activities.slice(0, displayLimit).map((activity, index) => {
              const learningPathLabel = getLearningPathLabel(activity, lang);

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
                          className={`inline-flex items-center rounded-full px-2 py-0.5 ${BADGE_TEXT_CLASS} font-medium ${getLearningPathBadgeClass(activity)}`}
                        >
                          {learningPathLabel}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-foreground line-clamp-2">
                      <span className="mr-1 inline-flex">
                        {(() => {
                          const Icon = getActivityIcon(activity);
                          return <Icon className="size-4" strokeWidth={1.5} />;
                        })()}
                      </span>
                      {getActivityText(activity, lang)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {formatTime(
                        activity.created_at || activity.timestamp,
                        lang
                      )}
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
