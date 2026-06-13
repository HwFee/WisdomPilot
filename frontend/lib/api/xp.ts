/**
 * XP (经验值) API Client
 */

import { fetchWithAuth } from './client'
import { API_BASE_URL } from './client'
import { getStoredToken } from './auth'

export interface XpBalance {
  balance: number
  level: string
}

export interface XpTransaction {
  id: string
  type: string
  category: string
  amount: number
  balance_after: number
  level_before: string
  level_after: string
  level_up: boolean
  reference_type?: string
  reference_id?: string
  description?: string
  created_at: string
}

export interface XpTransactionList {
  transactions: XpTransaction[]
  total: number
}

export async function getXpBalance(): Promise<XpBalance> {
  const token = getStoredToken()
  if (!token) {
    throw new Error('Not authenticated')
  }
  const response = await fetchWithAuth(`${API_BASE_URL}/api/xp/balance`, token)
  if (!response.ok) {
    throw new Error('Failed to fetch XP balance')
  }
  return response.json()
}

export async function getXpTransactions(
  limit: number = 20,
  offset: number = 0,
): Promise<XpTransactionList> {
  const token = getStoredToken()
  if (!token) {
    throw new Error('Not authenticated')
  }
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  })
  const response = await fetchWithAuth(
    `${API_BASE_URL}/api/xp/transactions?${params}`,
    token,
  )
  if (!response.ok) {
    throw new Error('Failed to fetch XP transactions')
  }
  return response.json()
}
