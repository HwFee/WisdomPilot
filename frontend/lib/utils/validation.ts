/**
 * Form validation utilities for login/register pages.
 *
 * TDD: Tests are in __tests__/validation.test.ts
 */

/**
 * Validation result type
 */
export interface ValidationResult {
  valid: boolean
  error?: string
}

/**
 * Password strength levels
 */
export type PasswordStrength = 'weak' | 'medium' | 'strong'

export interface PasswordValidationResult extends ValidationResult {
  strength?: PasswordStrength
  requirements?: {
    length: boolean
    letter: boolean
    digit: boolean
    special?: boolean
  }
}

/**
 * Email validation regex pattern
 */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Validate email format
 */
export function validateEmail(email: string): ValidationResult {
  if (!email || email.trim() === '') {
    return { valid: false, error: '请输入邮箱地址' }
  }

  if (!EMAIL_REGEX.test(email)) {
    return { valid: false, error: '请输入有效的邮箱地址' }
  }

  return { valid: true }
}

/**
 * Validate username
 * - 2-100 characters
 * - No special characters (only letters, numbers, underscores, Chinese)
 */
export function validateUsername(username: string): ValidationResult {
  if (!username || username.trim() === '') {
    return { valid: false, error: '请输入用户名' }
  }

  if (username.length < 2) {
    return { valid: false, error: '用户名至少需要2个字符' }
  }

  if (username.length > 100) {
    return { valid: false, error: '用户名不能超过100个字符' }
  }

  // Allow letters, numbers, underscores, and Chinese characters
  const validPattern = /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/
  if (!validPattern.test(username)) {
    return { valid: false, error: '用户名只能包含字母、数字、下划线和中文' }
  }

  return { valid: true }
}

/**
 * Validate password and calculate strength
 *
 * Requirements:
 * - At least 8 characters
 * - At least one letter
 * - At least one digit
 */
export function validatePassword(password: string): PasswordValidationResult {
  if (!password || password === '') {
    return { valid: false, error: '请输入密码' }
  }

  const requirements = {
    length: password.length >= 8,
    letter: /[a-zA-Z]/.test(password),
    digit: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  }

  const errors: string[] = []

  if (!requirements.length) {
    errors.push('密码长度至少需要8个字符')
  }
  if (!requirements.letter) {
    errors.push('密码需要包含至少一个字母')
  }
  if (!requirements.digit) {
    errors.push('密码需要包含至少一个数字')
  }

  if (errors.length > 0) {
    return {
      valid: false,
      error: errors.join('; '),
      requirements,
    }
  }

  // Calculate strength
  let strength: PasswordStrength = 'weak'
  if (requirements.length && requirements.letter && requirements.digit) {
    if (password.length >= 12 && requirements.special) {
      strength = 'strong'
    } else if (password.length >= 8) {
      strength = 'medium'
    }
  }

  return {
    valid: true,
    strength,
    requirements,
  }
}

/**
 * Validate password confirmation
 */
export function validatePasswordConfirm(
  password: string,
  confirm: string
): ValidationResult {
  if (!confirm || confirm === '') {
    return { valid: false, error: '请确认密码' }
  }

  if (password !== confirm) {
    return { valid: false, error: '两次输入的密码不一致' }
  }

  return { valid: true }
}

/**
 * Get password strength display info
 */
export function getPasswordStrengthInfo(strength: PasswordStrength): {
  label: string
  color: string
  width: string
} {
  switch (strength) {
    case 'weak':
      return { label: '弱', color: 'bg-red-500', width: '33%' }
    case 'medium':
      return { label: '中', color: 'bg-yellow-500', width: '66%' }
    case 'strong':
      return { label: '强', color: 'bg-green-500', width: '100%' }
    default:
      return { label: '', color: '', width: '0%' }
  }
}
