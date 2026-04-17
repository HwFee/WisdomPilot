/**
 * Favorites API - User favorites endpoints
 */

import {
  FavoriteCreate,
  FavoriteUpdate,
  FavoriteResponse,
  FavoriteListResponse,
  FavoriteCountResponse,
  FavoriteFoldersListResponse,
} from "@/types/api";
import { get, post, patch, del } from "./client";

// ========================================
// Check Types
// ========================================

export interface FavoriteCheckResponse {
  is_favorited: boolean;
  favorite_id: string | null;
}

// ========================================
// Favorites API Functions
// ========================================

export async function addFavorite(
  token: string,
  data: FavoriteCreate,
): Promise<FavoriteResponse> {
  return post<FavoriteResponse>("/api/favorites", token, data);
}

/**
 * Check if a specific exercise is already favorited.
 * For mastery path: pass chapterId.
 * For challenge path: omit chapterId (or pass undefined).
 * Uses the dedicated /check endpoint — much faster than loading all favorites.
 */
export async function checkFavorite(
  token: string,
  exerciseId: number,
  chapterId?: number,
): Promise<FavoriteCheckResponse> {
  let url = `/api/favorites/check?exercise_id=${exerciseId}`;
  if (chapterId !== undefined && chapterId !== null) {
    url += `&chapter_id=${chapterId}`;
  }
  return get<FavoriteCheckResponse>(url, token);
}

export async function getFavorites(
  token: string,
  limit: number = 50,
  offset: number = 0,
  folder?: string,
): Promise<FavoriteListResponse> {
  let url = `/api/favorites?limit=${limit}&offset=${offset}`;
  if (folder) {
    url += `&folder=${encodeURIComponent(folder)}`;
  }
  return get<FavoriteListResponse>(url, token);
}

export async function getFavoritesCount(
  token: string,
  folder?: string,
): Promise<FavoriteCountResponse> {
  let url = "/api/favorites/count";
  if (folder) {
    url += `?folder=${encodeURIComponent(folder)}`;
  }
  return get<FavoriteCountResponse>(url, token);
}

export async function getFavoriteFolders(
  token: string,
): Promise<FavoriteFoldersListResponse> {
  return get<FavoriteFoldersListResponse>("/api/favorites/folders", token);
}

export async function updateFavorite(
  token: string,
  favoriteId: string,
  data: FavoriteUpdate,
): Promise<FavoriteResponse> {
  return patch<FavoriteResponse>(`/api/favorites/${favoriteId}`, token, data);
}

export async function removeFavorite(
  token: string,
  favoriteId: string,
): Promise<{ success: boolean }> {
  return del<{ success: boolean }>(`/api/favorites/${favoriteId}`, token);
}

export async function batchRemoveFavorites(
  token: string,
  favoriteIds: string[],
): Promise<{ success: boolean; deleted_count: number }> {
  return post<{ success: boolean; deleted_count: number }>(
    "/api/favorites/batch-delete",
    token,
    favoriteIds,
  );
}

// Re-export types
export type {
  FavoriteCreate,
  FavoriteUpdate,
  FavoriteResponse,
  FavoriteListResponse,
  FavoriteCountResponse,
  FavoriteFoldersListResponse,
  FavoriteCheckResponse,
};
