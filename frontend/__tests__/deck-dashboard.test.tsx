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

    // P-01 推荐理由
    expect(screen.getByText('WHY THIS · 推荐理由')).toBeInTheDocument()
    expect(screen.getByText(/这一关专攻「边界条件处理」/)).toBeInTheDocument()

    // P-02 能力指纹已并入能力图谱：指纹码在图谱标题行
    expect(screen.queryByText('ABILITY FINGERPRINT · 能力指纹')).not.toBeInTheDocument()
    expect(screen.getByText('R4-D3-I5')).toBeInTheDocument()
    expect(screen.getAllByText(/至 LV\./).length).toBeGreaterThan(0)

    // 三轴能力图谱
    expect(screen.getAllByText('审阅').length).toBeGreaterThan(0)
    expect(screen.getAllByText('调试').length).toBeGreaterThan(0)
    expect(screen.getAllByText('实现').length).toBeGreaterThan(0)
    expect(screen.getAllByText('LV.4').length).toBeGreaterThan(0)

    // 四模块（导航里也有同名链接，断言至少各出现一次）
    expect(screen.getAllByText('代码审查室').length).toBeGreaterThan(0)
    expect(screen.getAllByText('调试竞技场').length).toBeGreaterThan(0)
    expect(screen.getByText('苏格拉底导师')).toBeInTheDocument()
    expect(screen.getByText('基本功认证')).toBeInTheDocument()

    // 情报区
    expect(screen.getByText('WEAK POINTS · 待攻克弱点')).toBeInTheDocument()
    expect(screen.getAllByText('边界条件处理').length).toBeGreaterThan(0)
    // P-04 弱点来源标注
    expect(screen.getByText('2天前 · 审查漏报')).toBeInTheDocument()
    expect(screen.getByText('FEED · 最近动态')).toBeInTheDocument()
  })
})
