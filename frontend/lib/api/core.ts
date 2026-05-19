/**
 * Core (智核) API Client
 * Handles all core currency related API calls
 */

import { fetchWithAuth } from './client';
import { API_BASE_URL } from './client';
import { getStoredToken } from './auth';

// Types
export interface CoreBalance {
  balance: number;
  total_earned: number;
  total_spent: number;
}

export type CoreSpendCategory = 'ai_hint_light' | 'ai_hint_medium' | 'ai_hint_deep';

export type CoreEarnCategory =
  | 'mastery'
  | 'arena'
  | 'checkin'
  | 'study_time'
  | 'daily_exercises'
  | 'daily_accuracy'
  | 'bonus';

export interface CoreTransaction {
  id: string;
  type: 'earn' | 'spend';
  category: string;
  amount: number;
  balance_after: number;
  reference_type?: string;
  reference_id?: string;
  description?: string;
  created_at: string;
}

export interface CoreTransactionList {
  transactions: CoreTransaction[];
  total: number;
}

export interface DailyCoreSummary {
  earned_today: number;
  spent_today: number;
  daily_exercises: number;
  daily_accuracy: number;
  pending_rewards: Record<string, number>;
}

export interface SpendRequest {
  amount: number;
  category: CoreSpendCategory;
  reference_type?: string;
  reference_id?: string;
  description?: string;
}

export interface SpendResult {
  success: boolean;
  balance_after: number;
  transaction_id: string;
}

/**
 * Get user's current core balance
 */
export async function getCoreBalance(): Promise<CoreBalance> {
  const token = getStoredToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  const response = await fetchWithAuth(`${API_BASE_URL}/api/cores/balance`, token);
  if (!response.ok) {
    throw new Error('Failed to fetch core balance');
  }
  return response.json();
}

/**
 * Spend cores for AI hints
 */
export async function spendCores(request: SpendRequest): Promise<SpendResult> {
  const token = getStoredToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  const response = await fetchWithAuth(`${API_BASE_URL}/api/cores/spend`, token, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to spend cores');
  }

  return response.json();
}

/**
 * Get transaction history
 */
export async function getCoreTransactions(
  limit: number = 20,
  offset: number = 0
): Promise<CoreTransactionList> {
  const token = getStoredToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  const response = await fetchWithAuth(`${API_BASE_URL}/api/cores/transactions?${params}`, token);
  if (!response.ok) {
    throw new Error('Failed to fetch transactions');
  }
  return response.json();
}

/**
 * Get daily core summary including pending rewards
 */
export async function getDailyCoreSummary(): Promise<DailyCoreSummary> {
  const token = getStoredToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  const response = await fetchWithAuth(`${API_BASE_URL}/api/cores/daily-summary`, token);
  if (!response.ok) {
    throw new Error('Failed to fetch daily summary');
  }
  return response.json();
}

/**
 * AI Hint costs (in cores)
 */
export const AI_HINT_COSTS = {
  light: 1,   // ai_hint_light
  medium: 3,  // ai_hint_medium
  deep: 5,    // ai_hint_deep
} as const;

/**
 * Check if user has enough cores for a hint
 */
export function hasEnoughCores(balance: number, hintType: keyof typeof AI_HINT_COSTS): boolean {
  return balance >= AI_HINT_COSTS[hintType];
}

/**
 * Core earning rewards configuration
 */
export const CORE_REWARDS = {
  // Mastery path
  mastery_exercise_correct: 2,
  mastery_chapter_complete: 10,
  mastery_course_complete: 20,

  // Challenge path
  arena_correct: 3,

  // Check-in
  checkin_base: 5,
  checkin_streak_3: 10,
  checkin_streak_7: 20,
  checkin_streak_14: 35,
  checkin_streak_30: 55,

  // Study time (per 30 minutes)
  study_time_30min: 5,

  // Daily exercises (challenge path)
  daily_exercises_5: 3,
  daily_exercises_10: 8,
  daily_exercises_20: 15,

  // Daily accuracy
  daily_accuracy_60: 5,
  daily_accuracy_80: 10,
  daily_accuracy_95: 20,
} as const;
