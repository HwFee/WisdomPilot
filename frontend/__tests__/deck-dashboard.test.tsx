/**
 * 训练舱首页渲染冒烟测试
 */
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { DashboardClient } from '@/components/dashboard/DashboardClient'
import { dashboardMock } from '@/lib/api/deck/mock/dashboard'

// matchMedia polyfill（CountUp / 键盘导航 / ThemeToggle 用到）
beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      onchange: null,
      dispatchEvent: jest.fn(),
    }),
  })
})

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/dashboard',
}))

jest.mock('@/lib/api', () => ({
  isAuthenticated: () => true,
  getStoredUser: () => ({ username: '清源' }),
  logout: jest.fn(),
}))

jest.mock('@/lib/api/deck/dashboard', () => ({
  getDeckDashboard: () => Promise.resolve(dashboardMock),
}))

describe('训练舱首页', () => {
  it('渲染主任务、三轴、四模块与情报区', async () => {
    render(<DashboardClient />)

    // 主任务
    await waitFor(() => expect(screen.getByText(/这段快速排序里有/)).toBeInTheDocument())
    expect(screen.getByText('TODAY\'S MISSION · 今日主任务')).toBeInTheDocument()

    // 三轴
    expect(screen.getByText('审阅')).toBeInTheDocument()
    expect(screen.getByText('调试')).toBeInTheDocument()
    expect(screen.getByText('实现')).toBeInTheDocument()
    expect(screen.getByText('LV.4')).toBeInTheDocument()

    // 四模块（导航里也有同名链接，断言至少各出现一次）
    expect(screen.getAllByText('代码审查室').length).toBeGreaterThan(0)
    expect(screen.getAllByText('调试竞技场').length).toBeGreaterThan(0)
    expect(screen.getByText('苏格拉底导师')).toBeInTheDocument()
    expect(screen.getByText('基本功认证')).toBeInTheDocument()

    // 情报区
    expect(screen.getByText('WEAK POINTS · 待攻克弱点')).toBeInTheDocument()
    expect(screen.getAllByText('边界条件处理').length).toBeGreaterThan(0)
    expect(screen.getByText('FEED · 最近动态')).toBeInTheDocument()
  })
})
