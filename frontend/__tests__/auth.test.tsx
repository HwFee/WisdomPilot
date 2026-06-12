/**
 * @jest-environment jsdom
 *
 * Swiss UI smoke test for RegisterPage.
 *
 * Replaces the previous animated-characters test suite, which asserted
 * behavior that was intentionally removed during the Swiss redesign
 * (language toggle, password strength meter, custom field validation,
 * post-register redirect to /login). The new Swiss UI redirects to
 * /dashboard and relies on browser-native validation.
 *
 * The thin contract validated here:
 *   - renders the register form (name + email + password + confirm-password)
 *   - calls the auth API on submit and navigates to /dashboard on success
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import RegisterPageClient from '../app/register/page-client'

// Mock next/navigation router
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: jest.fn(),
  }),
}))

// Mock the auth API (page-client calls register() directly)
const mockRegister = jest.fn()
jest.mock('../lib/api', () => ({
  register: (...args: unknown[]) => mockRegister(...args),
}))

describe('RegisterPage Swiss smoke test', () => {
  beforeEach(() => {
    mockPush.mockClear()
    mockRegister.mockReset()
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

  it('renders the register form: username, email, password, confirm-password, submit', () => {
    render(<RegisterPageClient />)

    // <input type="text"> and <input type="email"> have implicit role "textbox"
    expect(screen.getByRole('textbox', { name: /用户名/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /邮箱/i })).toBeInTheDocument()
    // Two password inputs share the same visible label "密码" — use getAllByLabelText
    expect(screen.getAllByLabelText(/^密码$/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByLabelText(/确认密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /注册/ })).toBeInTheDocument()
  })

  it('exposes a link back to /login', () => {
    render(<RegisterPageClient />)

    const loginLink = screen.getByRole('link', { name: /登录/ })
    expect(loginLink).toHaveAttribute('href', '/login')
  })

  it('submits credentials to register() and navigates to /dashboard on success', async () => {
    mockRegister.mockResolvedValueOnce({
      access_token: 'test-token',
      token_type: 'bearer',
      user: { id: '1', email: 'test@example.com', username: 'testuser' },
    })

    render(<RegisterPageClient />)

    fireEvent.change(screen.getByRole('textbox', { name: /用户名/i }), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: /邮箱/i }), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/^密码$/i), {
      target: { value: 'Password123' },
    })
    fireEvent.change(screen.getByLabelText(/确认密码/i), {
      target: { value: 'Password123' },
    })
    // Agree to terms (required by the form before submission)
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: /注册/ }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('test@example.com', 'testuser', 'Password123')
    })
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('shows a password mismatch error when confirm-password does not match', async () => {
    render(<RegisterPageClient />)

    fireEvent.change(screen.getByRole('textbox', { name: /用户名/i }), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: /邮箱/i }), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/^密码$/i), {
      target: { value: 'Password123' },
    })
    fireEvent.change(screen.getByLabelText(/确认密码/i), {
      target: { value: 'Different123' },
    })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: /注册/ }))

    await waitFor(() => {
      expect(screen.getByText('两次输入的密码不一致')).toBeInTheDocument()
    })
    expect(mockRegister).not.toHaveBeenCalled()
    expect(mockPush).not.toHaveBeenCalled()
  })
})