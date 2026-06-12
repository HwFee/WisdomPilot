/**
 * @jest-environment jsdom
 *
 * Swiss UI smoke test for LoginPage.
 *
 * Replaces the previous animated-characters test suite, which asserted
 * behavior that was intentionally removed during the Swiss redesign
 * (language toggle, password visibility, custom field validation).
 * The new tests only validate the contract that the Swiss UI commits to:
 *   - renders the login form (email + password + submit + register link)
 *   - calls the auth API on submit and navigates to /dashboard on success
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import LoginPageClient from '../app/login/page-client'

// Mock next/navigation router
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: jest.fn(),
  }),
}))

// Mock the auth API (page-client calls login() directly)
const mockLogin = jest.fn()
jest.mock('../lib/api', () => ({
  login: (...args: unknown[]) => mockLogin(...args),
}))

describe('LoginPage Swiss smoke test', () => {
  beforeEach(() => {
    mockPush.mockClear()
    mockLogin.mockReset()
    // Provide a sane localStorage so the api module's store calls don't crash
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn().mockReturnValue(null),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    })
  })

  it('renders the login form: email, password, submit button', () => {
    render(<LoginPageClient />)

    // <input type="email"> has implicit role "textbox"
    expect(screen.getByRole('textbox', { name: /邮箱/i })).toBeInTheDocument()
    // <input type="password"> is accessed via its label
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登录/ })).toBeInTheDocument()
  })

  it('exposes a link to /register and a link to /forgot-password', () => {
    render(<LoginPageClient />)

    const registerLink = screen.getByRole('link', { name: /注册/ })
    expect(registerLink).toHaveAttribute('href', '/register')

    const forgotLink = screen.getByRole('link', { name: /忘记密码/ })
    expect(forgotLink).toHaveAttribute('href', '/forgot-password')
  })

  it('submits credentials to login() and navigates to /dashboard on success', async () => {
    mockLogin.mockResolvedValueOnce({
      access_token: 'test-token',
      token_type: 'bearer',
      user: { id: '1', email: 'test@example.com', username: 'testuser' },
    })

    render(<LoginPageClient />)

    fireEvent.change(screen.getByRole('textbox', { name: /邮箱/i }), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'Password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /登录/ }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'Password123', false)
    })
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('surfaces the error message returned from login()', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'))

    render(<LoginPageClient />)

    fireEvent.change(screen.getByRole('textbox', { name: /邮箱/i }), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'wrongpassword' },
    })
    fireEvent.click(screen.getByRole('button', { name: /登录/ }))

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
    expect(mockPush).not.toHaveBeenCalled()
  })
})