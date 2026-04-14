/**
 * Tests for validation utilities
 *
 * TDD: These tests define the expected behavior of validation functions.
 */

import {
  validateEmail,
  validateUsername,
  validatePassword,
  validatePasswordConfirm,
  getPasswordStrengthInfo,
  PasswordStrength,
} from '../lib/utils/validation'

describe('validateEmail', () => {
  it('should reject empty email', () => {
    const result = validateEmail('')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('请输入')
  })

  it('should reject invalid email formats', () => {
    const invalidEmails = [
      'not-an-email',
      'missing@domain',
      '@nodomain.com',
      'spaces in@email.com',
    ]

    invalidEmails.forEach(email => {
      const result = validateEmail(email)
      expect(result.valid).toBe(false)
      expect(result.error).toBeDefined()
    })
  })

  it('should accept valid emails', () => {
    const validEmails = [
      'test@example.com',
      'user.name@domain.org',
      'user+tag@example.co.uk',
    ]

    validEmails.forEach(email => {
      const result = validateEmail(email)
      expect(result.valid).toBe(true)
      expect(result.error).toBeUndefined()
    })
  })
})

describe('validateUsername', () => {
  it('should reject empty username', () => {
    const result = validateUsername('')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('请输入')
  })

  it('should reject username shorter than 2 characters', () => {
    const result = validateUsername('a')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('2')
  })

  it('should reject username longer than 100 characters', () => {
    const longUsername = 'a'.repeat(101)
    const result = validateUsername(longUsername)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('100')
  })

  it('should reject special characters', () => {
    const result = validateUsername('user@name')
    expect(result.valid).toBe(false)
    expect(result.error).toBeDefined()
  })

  it('should accept valid usernames', () => {
    const validUsernames = [
      'ab',
      'testuser',
      'test_user',
      'TestUser123',
      '测试用户',
      '用户名',
    ]

    validUsernames.forEach(username => {
      const result = validateUsername(username)
      expect(result.valid).toBe(true)
    })
  })
})

describe('validatePassword', () => {
  it('should reject empty password', () => {
    const result = validatePassword('')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('请输入')
  })

  it('should reject password shorter than 8 characters', () => {
    const result = validatePassword('abc123')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('8')
  })

  it('should reject password without letter', () => {
    const result = validatePassword('12345678')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('字母')
  })

  it('should reject password without digit', () => {
    const result = validatePassword('abcdefgh')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('数字')
  })

  it('should accept valid passwords', () => {
    const validPasswords = [
      'password123',
      'Test1234',
      'abc123xyz',
    ]

    validPasswords.forEach(password => {
      const result = validatePassword(password)
      expect(result.valid).toBe(true)
    })
  })

  it('should calculate password strength correctly', () => {
    // Weak: only letters and digits, but valid
    const weakResult = validatePassword('abc123xy')  // 8 chars, letter+digit
    expect(weakResult.strength).toBe('medium')

    // Strong: 12+ chars with special character
    const strongResult = validatePassword('password123!@#')
    expect(strongResult.strength).toBe('strong')
  })

  it('should return requirements object', () => {
    const result = validatePassword('abc123')
    expect(result.requirements).toBeDefined()
    expect(result.requirements?.length).toBe(false)  // 6 chars < 8
    expect(result.requirements?.letter).toBe(true)
    expect(result.requirements?.digit).toBe(true)
  })
})

describe('validatePasswordConfirm', () => {
  it('should reject empty confirmation', () => {
    const result = validatePasswordConfirm('password123', '')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('请确认')
  })

  it('should reject mismatched passwords', () => {
    const result = validatePasswordConfirm('password123', 'password456')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('不一致')
  })

  it('should accept matching passwords', () => {
    const result = validatePasswordConfirm('password123', 'password123')
    expect(result.valid).toBe(true)
  })
})

describe('getPasswordStrengthInfo', () => {
  it('should return correct info for weak strength', () => {
    const info = getPasswordStrengthInfo('weak')
    expect(info.label).toBe('弱')
    expect(info.color).toContain('red')
    expect(info.width).toBe('33%')
  })

  it('should return correct info for medium strength', () => {
    const info = getPasswordStrengthInfo('medium')
    expect(info.label).toBe('中')
    expect(info.color).toContain('yellow')
    expect(info.width).toBe('66%')
  })

  it('should return correct info for strong strength', () => {
    const info = getPasswordStrengthInfo('strong')
    expect(info.label).toBe('强')
    expect(info.color).toContain('green')
    expect(info.width).toBe('100%')
  })
})
