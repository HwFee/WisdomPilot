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
  exerciseId: number;
  chapterId?: number;
  subsectionIndex?: number;
  /** Source context: 'mastery' for 精进之路, 'arena' for 挑战之路 */
  source?: "mastery" | "arena";
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  lang?: "zh" | "en";
  onFavoriteChange?: (isFavorited: boolean) => void;
}

export function FavoriteButton({
  exerciseId,
  chapterId,
  subsectionIndex = 0,
  source,
  size = "md",
  showLabel = false,
  lang = "zh",
  onFavoriteChange,
}: FavoriteButtonProps) {
  const [isFavorited, setIsFavorited] = useState(false);
  const [favoriteId, setFavoriteId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const t = (zh: string, en: string) => (lang === "zh" ? zh : en);

  // Determine which chapterId to use for the check/add call:
  // - mastery path: always pass chapterId so records are distinguished per chapter
  // - arena path: omit chapterId (NULL) so records are distinguished from mastery
  const effectiveChapterId =
    source === "mastery" || chapterId !== undefined ? chapterId : undefined;

  // Use the dedicated /check endpoint — O(1) instead of loading all 100 favorites
  useEffect(() => {
    let cancelled = false;

    const checkStatus = async () => {
      const token = getStoredToken();
      if (!token) return;

      try {
        const result = await checkFavorite(
          token,
          exerciseId,
          effectiveChapterId,
        );
        if (cancelled) return;
        setIsFavorited(result.is_favorited);
        setFavoriteId(result.favorite_id);
      } catch {
        // Silently handle — user might not be logged in or network issue
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
  }, [exerciseId, effectiveChapterId]);

  const handleToggleFavorite = useCallback(async () => {
    const token = getStoredToken();
    if (!token) return;

    setIsLoading(true);
    try {
      if (isFavorited && favoriteId) {
        await removeFavorite(token, favoriteId);
        setIsFavorited(false);
        setFavoriteId(null);
        onFavoriteChange?.(false);
      } else {
        const data: FavoriteCreate = {
          exercise_id: exerciseId,
          chapter_id: effectiveChapterId,
          subsection_index: subsectionIndex,
        };
        const response = await addFavorite(token, data);
        setIsFavorited(true);
        setFavoriteId(response.id);
        onFavoriteChange?.(true);
      }
    } catch (error) {
      console.error("[收藏] 操作失败:", error);
    } finally {
      setIsLoading(false);
    }
  }, [
    isFavorited,
    favoriteId,
    exerciseId,
    effectiveChapterId,
    subsectionIndex,
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
