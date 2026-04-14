/**
 * Favorites API - User favorites endpoints
 */

import {
  FavoriteCreate,
  FavoriteResponse,
  FavoriteListResponse,
  FavoriteCountResponse,
} from '@/types/api'
import { get, post, del } from './client'

// ========================================
// Favorites API Functions
// ========================================

export async function addFavorite(
  token: string,
  data: FavoriteCreate
): Promise<FavoriteResponse> {
  return post<FavoriteResponse>('/api/favorites', token, data)
}

export async function getFavorites(
  token: string,
  limit: number = 50,
  offset: number = 0
): Promise<FavoriteListResponse> {
  return get<FavoriteListResponse>(`/api/favorites?limit=${limit}&offset=${offset}`, token)
}

export async function getFavoritesCount(token: string): Promise<FavoriteCountResponse> {
  return get<FavoriteCountResponse>('/api/favorites/count', token)
}

export async function removeFavorite(
  token: string,
  favoriteId: string
): Promise<{ success: boolean }> {
  return del<{ success: boolean }>(`/api/favorites/${favoriteId}`, token)
}

// Re-export types
export type {
  FavoriteCreate,
  FavoriteResponse,
  FavoriteListResponse,
  FavoriteCountResponse,
}
