/**
 * API Module - Re-export from modular API structure
 * This file maintains backward compatibility while using the new modular API
 */

// Re-export everything from the modular API
export * from './api/index'

// Additional backward-compatible exports
export interface ApiError {
  detail: string
}

// Old interface aliases for backward compatibility
export interface AuthResponse {
  access_token: string
  token_type: string
  user: import('./api/index').User
}
