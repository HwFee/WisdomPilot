/**
 * API Types - Aligned with Backend Schemas
 * 训练舱重构后仅保留认证所需类型；领域类型在 lib/api/deck/types.ts。
 */

// ========================================
// User Types (from user.py)
// ========================================

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  is_admin: boolean
  created_at: string
  updated_at: string
}

export interface Token {
  access_token: string
  token_type: string
  user: User
}

export interface UserLogin {
  email: string
  password: string
  remember_me?: boolean
}

export interface UserCreate {
  email: string
  username: string
  password: string
}

// ========================================
// API Response Wrapper
// ========================================

export interface ApiError {
  detail: string
}
