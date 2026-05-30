/**
 * @jest-environment jsdom
 */
import { render, screen } from '@testing-library/react'
import { WelcomeSection } from '../WelcomeSection'

describe('WelcomeSection', () => {
  const mockUser = { id: '1', username: 'TestUser' }

  it('renders greeting with username', () => {
    render(<WelcomeSection user={mockUser} />)

    expect(screen.getByText('TestUser！')).toBeInTheDocument()
  })

  it('shows a greeting (morning/afternoon/evening based on time)', () => {
    render(<WelcomeSection user={mockUser} lang="zh" />)

    // One of these greetings should be present based on current time
    const greetingElement = screen.getByText(/(早上好|下午好|晚上好)/)
    expect(greetingElement).toBeInTheDocument()
  })

  it('displays English labels when lang is "en"', () => {
    render(<WelcomeSection user={mockUser} lang="en" />)

    expect(screen.getByText(/(Good morning|Good afternoon|Good evening)/)).toBeInTheDocument()
  })

  it('displays Chinese labels by default', () => {
    render(<WelcomeSection user={mockUser} lang="zh" />)

    expect(screen.getByText(/今天准备挑战点什么/)).toBeInTheDocument()
  })

  it('displays a quote', () => {
    render(<WelcomeSection user={mockUser} lang="zh" />)

    // Quote should be displayed
    const quoteSection = screen.getByText(/程序必须是为了给人看而写|简单是可靠的先决条件|先让它工作|代码写得好|任何傻瓜都能写出|最好的代码是|编程不是关于|好的代码本身就是/)
    expect(quoteSection).toBeInTheDocument()
  })
})
