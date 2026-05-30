/**
 * Form validation utilities for login/register pages.
 *
 * TDD: Tests are in __tests__/validation.test.ts
 */

/**
 * Supported languages
 */
export type Lang = 'zh' | 'en'

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
 * Error messages with i18n support
 */
const ERROR_MESSAGES = {
  email: {
    empty: { zh: '请输入邮箱地址', en: 'Please enter email address' },
    invalid: { zh: '请输入有效的邮箱地址', en: 'Please enter a valid email address' },
  },
  username: {
    empty: { zh: '请输入用户名', en: 'Please enter username' },
    tooShort: { zh: '用户名至少需要2个字符', en: 'Username must be at least 2 characters' },
    tooLong: { zh: '用户名不能超过100个字符', en: 'Username cannot exceed 100 characters' },
    invalidChars: { zh: '用户名只能包含字母、数字、下划线和中文', en: 'Username can only contain letters, numbers, underscores and Chinese' },
  },
  password: {
    empty: { zh: '请输入密码', en: 'Please enter password' },
    tooShort: { zh: '密码长度至少需要8个字符', en: 'Password must be at least 8 characters' },
    noLetter: { zh: '密码需要包含至少一个字母', en: 'Password must contain at least one letter' },
    noDigit: { zh: '密码需要包含至少一个数字', en: 'Password must contain at least one digit' },
  },
  passwordConfirm: {
    empty: { zh: '请确认密码', en: 'Please confirm password' },
    mismatch: { zh: '两次输入的密码不一致', en: 'Passwords do not match' },
  },
}

/**
 * Helper to get message by language
 */
function t(messages: { zh: string; en: string }, lang: Lang): string {
  return messages[lang]
}

/**
 * Validate email format
 */
export function validateEmail(email: string, lang: Lang = 'zh'): ValidationResult {
  if (!email || email.trim() === '') {
    return { valid: false, error: t(ERROR_MESSAGES.email.empty, lang) }
  }

  if (!EMAIL_REGEX.test(email)) {
    return { valid: false, error: t(ERROR_MESSAGES.email.invalid, lang) }
  }

  return { valid: true }
}

/**
 * Validate username
 * - 2-100 characters
 * - No special characters (only letters, numbers, underscores, Chinese)
 */
export function validateUsername(username: string, lang: Lang = 'zh'): ValidationResult {
  if (!username || username.trim() === '') {
    return { valid: false, error: t(ERROR_MESSAGES.username.empty, lang) }
  }

  if (username.length < 2) {
    return { valid: false, error: t(ERROR_MESSAGES.username.tooShort, lang) }
  }

  if (username.length > 100) {
    return { valid: false, error: t(ERROR_MESSAGES.username.tooLong, lang) }
  }

  // Allow letters, numbers, underscores, and Chinese characters
  const validPattern = /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/
  if (!validPattern.test(username)) {
    return { valid: false, error: t(ERROR_MESSAGES.username.invalidChars, lang) }
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
export function validatePassword(password: string, lang: Lang = 'zh'): PasswordValidationResult {
  if (!password || password === '') {
    return { valid: false, error: t(ERROR_MESSAGES.password.empty, lang) }
  }

  const requirements = {
    length: password.length >= 8,
    letter: /[a-zA-Z]/.test(password),
    digit: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  }

  const errors: string[] = []

  if (!requirements.length) {
    errors.push(t(ERROR_MESSAGES.password.tooShort, lang))
  }
  if (!requirements.letter) {
    errors.push(t(ERROR_MESSAGES.password.noLetter, lang))
  }
  if (!requirements.digit) {
    errors.push(t(ERROR_MESSAGES.password.noDigit, lang))
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
  confirm: string,
  lang: Lang = 'zh'
): ValidationResult {
  if (!confirm || confirm === '') {
    return { valid: false, error: t(ERROR_MESSAGES.passwordConfirm.empty, lang) }
  }

  if (password !== confirm) {
    return { valid: false, error: t(ERROR_MESSAGES.passwordConfirm.mismatch, lang) }
  }

  return { valid: true }
}

/**
 * Get password strength display info
 */
export function getPasswordStrengthInfo(
  strength: PasswordStrength,
  lang: Lang = 'zh'
): {
  label: string
  color: string
  width: string
} {
  const labels = {
    weak: { zh: '弱', en: 'Weak' },
    medium: { zh: '中', en: 'Medium' },
    strong: { zh: '强', en: 'Strong' },
  }

  switch (strength) {
    case 'weak':
      return { label: labels.weak[lang], color: 'bg-red-500', width: '33%' }
    case 'medium':
      return { label: labels.medium[lang], color: 'bg-yellow-500', width: '66%' }
    case 'strong':
      return { label: labels.strong[lang], color: 'bg-green-500', width: '100%' }
    default:
      return { label: '', color: '', width: '0%' }
  }
}
