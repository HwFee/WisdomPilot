/**
 * Auth API - Authentication endpoints
 */

import {
  User,
  Token,
  UserLogin,
  UserCreate,
} from '@/types/api'
import { postPublic, get, API_BASE_URL } from './client'

// ========================================
// Local Storage Helpers
// ========================================

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null
  const userStr = localStorage.getItem('user')
  if (!userStr) return null
  try {
    return JSON.parse(userStr) as User
  } catch {
    return null
  }
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token')
}

export function logout(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export function isAuthenticated(): boolean {
  return !!getStoredToken()
}

// ========================================
// Auth API Functions
// ========================================

export async function register(
  email: string,
  username: string,
  password: string
): Promise<Token> {
  const data = await postPublic<Token>('/api/auth/register', {
    email,
    username,
    password,
  } as UserCreate)

  // Store token in localStorage
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))

  return data
}

export async function login(email: string, password: string): Promise<Token> {
  const data = await postPublic<Token>('/api/auth/login', {
    email,
    password,
  } as UserLogin)

  // Store token in localStorage
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))

  return data
}

export async function getCurrentUser(token: string): Promise<User> {
  return get<User>('/api/auth/me', token)
}

export async function forgotPassword(email: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to send reset email')
  }
}

// Re-export types for convenience
export type { User, Token }
