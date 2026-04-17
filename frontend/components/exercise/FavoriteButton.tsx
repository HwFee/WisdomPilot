"use client";

import { useState, useCallback, useEffect } from "react";
import { Star } from "lucide-react";
import { getStoredToken } from "@/lib/api";
import {
  addFavorite,
  removeFavorite,
  checkFavorite,
} from "@/lib/api/favorites";
import type { FavoriteCreate } from "@/types/api";

interface FavoriteButtonProps {
  /** 题目标识 (格式: mastery-{courseId}-{chapterId}-{exerciseId} 或 arena-{courseId}-{exerciseId}) */
  exerciseKey?: string;
  /** 课程ID */
  courseId: number;
  /** 原始练习题ID */
  exerciseId?: number;
  /** 章节ID（精进之路来源） */
  chapterId?: number;
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
  const [favoriteId, setFavoriteId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const t = (zh: string, en: string) => (lang === "zh" ? zh : en);

  // 检查收藏状态 - 与错题本一致
  useEffect(() => {
    let cancelled = false;

    const checkStatus = async () => {
      const token = getStoredToken();
      if (!token) return;

      // 如果没有 exerciseKey 和 exerciseId，跳过检查
      if (!exerciseKey && !exerciseId) return;

      try {
        const result = await checkFavorite(token, exerciseKey, exerciseId);
        if (cancelled) return;
        setIsFavorited(result.is_favorited);
        setFavoriteId(result.favorite_id);
      } catch {
        if (!cancelled) {
          setIsFavorited(false);
          setFavoriteId(null);
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

    setIsLoading(true);
    try {
      if (isFavorited && favoriteId) {
        await removeFavorite(token, favoriteId);
        setIsFavorited(false);
        setFavoriteId(null);
        onFavoriteChange?.(false);
      } else {
        // 与错题本完全一致的请求格式
        const data: FavoriteCreate = {
          exercise_key: exerciseKey || "",
          course_id: courseId,
          exercise_id: exerciseId,
          chapter_id: chapterId,
          exercise_content: exerciseContent,
          exercise_type: exerciseType,
          exercise_difficulty: exerciseDifficulty,
          knowledge_points: knowledgePoints,
        };
        const response = await addFavorite(token, data);
        setIsFavorited(true);
        setFavoriteId(response.id);
        onFavoriteChange?.(true);
      }
    } catch {
      // 静默处理错误
    } finally {
      setIsLoading(false);
    }
  }, [
    isFavorited,
    favoriteId,
    exerciseKey,
    courseId,
    exerciseId,
    chapterId,
    exerciseContent,
    exerciseType,
    exerciseDifficulty,
    knowledgePoints,
    onFavoriteChange,
  ]);

  const sizeClasses = {
    sm: "w-6 h-6",
    md: "w-8 h-8",
    lg: "w-10 h-10",
  };

  const iconSizes = {
    sm: "w-3.5 h-3.5",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        handleToggleFavorite();
      }}
      disabled={isLoading}
      className={`
        flex items-center justify-center rounded-lg transition-all duration-200
        ${showLabel ? "px-2.5 gap-1" : sizeClasses[size]}
        ${
          isFavorited
            ? "bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30"
            : "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-yellow-500"
        }
        ${isLoading ? "opacity-50 cursor-not-allowed" : ""}
      `}
      title={
        isFavorited
          ? t("取消收藏", "Remove from favorites")
          : t("收藏", "Add to favorites")
      }
    >
      <Star
        className={`${iconSizes[size]} ${isFavorited ? "fill-yellow-500 text-yellow-500" : ""}`}
      />
      {showLabel && (
        <span className="text-sm">
          {isFavorited ? t("已收藏", "Favorited") : t("收藏", "Favorite")}
        </span>
      )}
    </button>
  );
}
