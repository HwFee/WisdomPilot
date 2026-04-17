/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Component as RegisterPage } from '../components/ui/animated-characters-register-page'

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock the API
jest.mock('../lib/api', () => ({
  register: jest.fn(),
}))

// Mock the animated characters component
jest.mock('../components/ui/animated-characters', () => ({
  CharacterGroup: () => <div data-testid="character-group">Characters</div>,
}))

// Mock password strength indicator
jest.mock('../components/ui/password-strength-indicator', () => ({
  PasswordStrengthIndicator: () => <div data-testid="password-strength">Strength</div>,
}))

import { register } from '../lib/api'

const mockRegister = register as jest.MockedFunction<typeof register>

describe('Register Page', () => {
  beforeEach(() => {
    mockRegister.mockClear()
    mockPush.mockClear()
    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    }
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })
  })

  it('renders registration form in Chinese by default', () => {
    render(<RegisterPage />)

    expect(screen.getByText('创建账号')).toBeInTheDocument()
    expect(screen.getByText('用户名')).toBeInTheDocument()
    expect(screen.getByText('邮箱地址')).toBeInTheDocument()
    expect(screen.getByText('密码')).toBeInTheDocument()
    expect(screen.getByText('确认密码')).toBeInTheDocument()
  })

  it('switches to English when lang is changed', () => {
    render(<RegisterPage />)

    // Click English button
    fireEvent.click(screen.getByText('EN'))

    expect(screen.getByText('Create your account')).toBeInTheDocument()
    expect(screen.getByText('Username')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('Password')).toBeInTheDocument()
    expect(screen.getByText('Confirm Password')).toBeInTheDocument()
  })

  it('shows validation errors in Chinese', async () => {
    render(<RegisterPage />)

    // Fill in invalid email
    const emailInput = screen.getByPlaceholderText('you@example.com')
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.blur(emailInput)

    await waitFor(() => {
      expect(screen.getByText(/请输入有效的邮箱地址/)).toBeInTheDocument()
    })
  })

  it('shows validation errors in English when lang is en', async () => {
    render(<RegisterPage />)

    // Switch to English
    fireEvent.click(screen.getByText('EN'))

    // Fill in invalid email
    const emailInput = screen.getByPlaceholderText('you@example.com')
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.blur(emailInput)

    await waitFor(() => {
      expect(screen.getByText(/valid email/)).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    mockRegister.mockResolvedValueOnce({
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        is_active: true,
        is_admin: false,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    })

    render(<RegisterPage />)

    // Fill in form
    fireEvent.change(screen.getByPlaceholderText('username'), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('至少8个字符'), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByPlaceholderText('再次输入密码'), { target: { value: 'Password123' } })

    // Check terms checkbox
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)

    // Submit
    fireEvent.click(screen.getByText('注册'))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('test@example.com', 'testuser', 'Password123')
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  it('shows error when terms not agreed', async () => {
    render(<RegisterPage />)

    // Fill in form without checking terms
    fireEvent.change(screen.getByPlaceholderText('username'), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('至少8个字符'), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByPlaceholderText('再次输入密码'), { target: { value: 'Password123' } })

    // Submit without checking terms
    fireEvent.click(screen.getByText('注册'))

    await waitFor(() => {
      expect(screen.getByText(/请同意/)).toBeInTheDocument()
    })
  })

  it('shows error when passwords do not match on submit', async () => {
    render(<RegisterPage />)

    // Fill in form with mismatched passwords
    fireEvent.change(screen.getByPlaceholderText('username'), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('至少8个字符'), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByPlaceholderText('再次输入密码'), { target: { value: 'Different123' } })

    // Check terms
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)

    // Submit to trigger validation
    fireEvent.click(screen.getByText('注册'))

    await waitFor(() => {
      // The error message appears in multiple places:
      // 1. In the red alert box at the top of the form
      // 2. Under the confirm password field
      // Use getAllByText since there are multiple matching elements
      const errorElements = screen.getAllByText('两次输入的密码不一致')
      expect(errorElements.length).toBeGreaterThan(0)
    })
  })
})
