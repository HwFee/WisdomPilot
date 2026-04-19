import { render, screen } from '@testing-library/react'
import { Navbar } from './Navbar'

// Mock useRouter
const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
}

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
}))

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Sparkles: () => <span data-testid="sparkles-icon">Sparkles</span>,
  Code2: () => <span data-testid="code-icon">Code</span>,
  Search: () => <span data-testid="search-icon">Search</span>,
  LogOut: () => <span data-testid="logout-icon">Logout</span>,
  User: () => <span data-testid="user-icon">User</span>,
  Settings: () => <span data-testid="settings-icon">Settings</span>,
}))

describe('Navbar', () => {
  const mockUser = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
  }

  it('renders logo and title', () => {
    render(
      <Navbar
        user={mockUser}
        isLoggedIn={true}
        cores={50}
        xp={100}
      />
    )
    expect(screen.getByText('GAI 编程教学平台')).toBeInTheDocument()
  })

  it('renders user info when logged in', () => {
    render(
      <Navbar
        user={mockUser}
        isLoggedIn={true}
        cores={50}
        xp={100}
      />
    )
    expect(screen.getByText('testuser')).toBeInTheDocument()
  })

  it('renders login/register buttons when logged out', () => {
    render(
      <Navbar
        user={null}
        isLoggedIn={false}
        cores={0}
        xp={0}
      />
    )
    expect(screen.getByText('登录')).toBeInTheDocument()
    expect(screen.getByText('免费注册')).toBeInTheDocument()
  })

  it('renders navigation tabs', () => {
    render(
      <Navbar
        user={mockUser}
        isLoggedIn={true}
        cores={50}
        xp={100}
      />
    )
    expect(screen.getByText('仪表盘')).toBeInTheDocument()
    expect(screen.getByText('我的课程')).toBeInTheDocument()
    expect(screen.getByText('排行榜')).toBeInTheDocument()
  })

  it('renders cores and XP when logged in', () => {
    render(
      <Navbar
        user={mockUser}
        isLoggedIn={true}
        cores={50}
        xp={100}
      />
    )
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText('100 XP')).toBeInTheDocument()
  })
})
