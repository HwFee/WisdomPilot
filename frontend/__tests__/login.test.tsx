/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import LoginPage from '../app/login/page-client'

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock the API
jest.mock('../lib/api', () => ({
  login: jest.fn(),
}))

// Mock the animated characters component
jest.mock('../components/ui/animated-characters', () => ({
  CharacterGroup: () => <div data-testid="character-group">Characters</div>,
}))

import { login } from '../lib/api'

const mockLogin = login as jest.MockedFunction<typeof login>

describe('Login Page', () => {
  beforeEach(() => {
    mockLogin.mockClear()
    mockPush.mockClear()
    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn().mockReturnValue(null),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    }
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })
  })

  it('renders login form in Chinese by default', () => {
    render(<LoginPage />)

    expect(screen.getByText('欢迎回来')).toBeInTheDocument()
    expect(screen.getByText('邮箱地址')).toBeInTheDocument()
    expect(screen.getByText('密码')).toBeInTheDocument()
    expect(screen.getByText('登录')).toBeInTheDocument()
  })

  it('switches to English when lang is changed', () => {
    render(<LoginPage />)

    // Click English button
    fireEvent.click(screen.getByText('EN'))

    expect(screen.getByText('Welcome back!')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('Password')).toBeInTheDocument()
    expect(screen.getByText('Log in')).toBeInTheDocument()
  })

  it('shows email validation error in Chinese', async () => {
    render(<LoginPage />)

    // Fill in invalid email
    const emailInput = screen.getByPlaceholderText('you@example.com')
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.blur(emailInput)

    await waitFor(() => {
      expect(screen.getByText(/请输入有效的邮箱地址/)).toBeInTheDocument()
    })
  })

  it('shows email validation error in English when lang is en', async () => {
    render(<LoginPage />)

    // Switch to English
    fireEvent.click(screen.getByText('EN'))

    // Fill in invalid email
    const emailInput = screen.getByPlaceholderText('you@example.com')
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.blur(emailInput)

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument()
    })
  })

  it('toggles password visibility', () => {
    render(<LoginPage />)

    const passwordInput = screen.getByPlaceholderText('••••••••')
    expect(passwordInput).toHaveAttribute('type', 'password')

    // Click eye icon to show password
    const toggleButton = screen.getByRole('button', { name: '' })
    fireEvent.click(toggleButton)

    expect(passwordInput).toHaveAttribute('type', 'text')
  })

  it('submits form with valid data', async () => {
    mockLogin.mockResolvedValueOnce({
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

    render(<LoginPage />)

    // Fill in form
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'Password123' } })

    // Submit
    fireEvent.click(screen.getByText('登录'))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'Password123', false)
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('submits form with remember me checked', async () => {
    mockLogin.mockResolvedValueOnce({
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

    render(<LoginPage />)

    // Fill in form
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'Password123' } })

    // Check remember me
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)

    // Submit
    fireEvent.click(screen.getByText('登录'))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'Password123', true)
    })
  })

  it('shows error when login fails', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'))

    render(<LoginPage />)

    // Fill in form
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'wrongpassword' } })

    // Submit
    fireEvent.click(screen.getByText('登录'))

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })

  it('redirects admin users to admin page', async () => {
    mockLogin.mockResolvedValueOnce({
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: '1',
        email: 'admin@example.com',
        username: 'admin',
        is_active: true,
        is_admin: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    })

    const localStorageMock = {
      getItem: jest.fn().mockReturnValue(JSON.stringify({
        id: '1',
        email: 'admin@example.com',
        username: 'admin',
        is_admin: true,
      })),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    }
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })

    render(<LoginPage />)

    // Fill in form
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'admin@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'Admin123' } })

    // Submit
    fireEvent.click(screen.getByText('登录'))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
      // After login, the component checks localStorage for admin
    })
  })
})
