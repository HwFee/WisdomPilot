"use client";

import { useState, useCallback, useEffect, useRef, useTransition } from "react";
import { Star } from "lucide-react";
import { getStoredToken } from "@/lib/api";
import {
  addFavorite,
  removeFavorite,
  checkFavorite,
} from "@/lib/api/favorites";
import type { FavoriteCreate } from "@/types/api";

const SIZE_CLASSES = {
  sm: "size-6",
  md: "size-8",
  lg: "size-10",
};

const ICON_SIZES = {
  sm: "size-3.5",
  md: "size-4",
  lg: "size-5",
};

interface FavoriteButtonProps {
  /** 题目标识 (格式: mastery-{courseId}-{chapterId}-{exerciseId} 或 arena-{courseId}-{exerciseId} 或 enhanced-{courseId}-{sectionId}-{exerciseId}) */
  exerciseKey?: string;
  /** 课程ID */
  courseId?: number;
  /** 原始练习题ID */
  exerciseId?: number;
  /** 章节ID（精进之路来源） */
  chapterId?: number;
  /** 小节ID（强化测试来源） */
  sectionId?: number;
  /** 题目内容快照 */
  exerciseContent?: {
    title?: string;
    text?: string;
    description?: string;
    options?: string[];
  };
  /** 题目类型 */
  exerciseType?: string;
  /** 题目难度 */
  exerciseDifficulty?: number;
  /** 知识点 */
  knowledgePoints?: string[];
  /** 尺寸 */
  size?: "sm" | "md" | "lg";
  /** 是否显示标签 */
  showLabel?: boolean;
  /** 语言 */
  lang?: "zh" | "en";
  /** 收藏状态变化回调 */
  onFavoriteChange?: (isFavorited: boolean) => void;
}

export function FavoriteButton({
  exerciseKey,
  courseId,
  exerciseId,
  chapterId,
  sectionId,
  exerciseContent,
  exerciseType,
  exerciseDifficulty,
  knowledgePoints,
  size = "md",
  showLabel = false,
  lang = "zh",
  onFavoriteChange,
}: FavoriteButtonProps) {
  const [isFavorited, setIsFavorited] = useState(false);
  const favoriteIdRef = useRef<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const t = (zh: string, en: string) => (lang === "zh" ? zh : en);

  // 检查收藏状态 - 与错题本一致
  useEffect(() => {
    let cancelled = false;

    const checkStatus = async () => {
      const token = getStoredToken();
      if (!token) return;

      // 如果没有 exerciseKey 和 exerciseId，跳过检查
      if (!exerciseKey && !exerciseId) return;

      console.log("[FavoriteButton] checkStatus called:", { exerciseKey, exerciseId, courseId });

      try {
        const result = await checkFavorite(token, exerciseKey, exerciseId);
        console.log("[FavoriteButton] checkStatus result:", result);
        if (cancelled) return;
        setIsFavorited(result.is_favorited);
        favoriteIdRef.current = result.favorite_id;
      } catch (error) {
        console.error("[FavoriteButton] checkStatus error:", error);
        if (!cancelled) {
          setIsFavorited(false);
          favoriteIdRef.current = null;
        }
      }
    };

    checkStatus();
    return () => {
      cancelled = true;
    };
  }, [exerciseKey, exerciseId]);

  const handleToggleFavorite = useCallback(async () => {
    const token = getStoredToken();
    if (!token) return;

    // 如果没有 exerciseKey 和 exerciseId，无法收藏
    if (!exerciseKey && !exerciseId) return;

    console.log("[FavoriteButton] handleToggleFavorite:", {
      isFavorited,
      favoriteIdRef,
      exerciseKey,
      exerciseId,
      courseId,
    });

    startTransition(async () => {
      try {
        if (isFavorited && favoriteIdRef.current) {
          console.log("[FavoriteButton] Removing favorite:", favoriteIdRef.current);
          await removeFavorite(token, favoriteIdRef.current);
          setIsFavorited(false);
          favoriteIdRef.current = null;
          onFavoriteChange?.(false);
        } else {
          // 与错题本完全一致的请求格式
          const data: FavoriteCreate = {
            exercise_key: exerciseKey || "",
            course_id: courseId ?? 0,
            exercise_id: exerciseId,
            chapter_id: chapterId,
            section_id: sectionId,
            exercise_content: exerciseContent,
            exercise_type: exerciseType,
            exercise_difficulty: exerciseDifficulty,
            knowledge_points: knowledgePoints,
          };
          console.log("[FavoriteButton] Adding favorite:", data);
          const response = await addFavorite(token, data);
          console.log("[FavoriteButton] Add favorite response:", response);
          setIsFavorited(true);
          favoriteIdRef.current = response.id;
          onFavoriteChange?.(true);
        }
      } catch (error) {
        console.error("[FavoriteButton] handleToggleFavorite error:", error);
      }
    });
  }, [
    isFavorited,
    favoriteIdRef,
    exerciseKey,
    courseId,
    exerciseId,
    chapterId,
    sectionId,
    exerciseContent,
    exerciseType,
    exerciseDifficulty,
    knowledgePoints,
    onFavoriteChange,
  ]);

  return (
    <button type="button"
      onClick={(e) => {
        e.stopPropagation();
        handleToggleFavorite();
      }}
      disabled={isPending}
      className={`
        flex items-center justify-center rounded-lg transition-all duration-200
        ${showLabel ? "px-2.5 gap-1" : SIZE_CLASSES[size]}
        ${
          isFavorited
            ? "bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30"
            : "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-yellow-500"
        }
        ${isPending ? "opacity-50 cursor-not-allowed" : ""}
      `}
      title={
        isFavorited
          ? t("取消收藏", "Remove from favorites")
          : t("收藏", "Add to favorites")
      }
    >
      <Star
        className={`${ICON_SIZES[size]} ${isFavorited ? "fill-yellow-500 text-yellow-500" : ""}`}
      />
      {showLabel && (
        <span className="text-sm">
          {isFavorited ? t("已收藏", "Favorited") : t("收藏", "Favorite")}
        </span>
      )}
    </button>
  );
}
