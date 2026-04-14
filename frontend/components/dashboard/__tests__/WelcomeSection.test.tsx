/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { WelcomeSection } from '../WelcomeSection'

describe('WelcomeSection', () => {
  const mockUser = { id: '1', username: 'TestUser' }
  const mockLastProgress = {
    courseName: 'C语言',
    chapterName: '第3章 循环',
  }

  it('renders greeting with username', () => {
    render(<WelcomeSection user={mockUser} onContinueLearning={() => {}} />)

    expect(screen.getByText('TestUser！')).toBeInTheDocument()
  })

  it('shows a greeting (morning/afternoon/evening based on time)', () => {
    render(<WelcomeSection user={mockUser} onContinueLearning={() => {}} lang="zh" />)

    // One of these greetings should be present based on current time
    const greetingElement = screen.getByText(/(早上好|下午好|晚上好)/)
    expect(greetingElement).toBeInTheDocument()
  })

  it('displays last progress when provided', () => {
    render(
      <WelcomeSection
        user={mockUser}
        lastProgress={mockLastProgress}
        onContinueLearning={() => {}}
        lang="zh"
      />
    )

    expect(screen.getByText(/C语言/)).toBeInTheDocument()
    expect(screen.getByText(/第3章 循环/)).toBeInTheDocument()
  })

  it('does not display last progress when null', () => {
    render(
      <WelcomeSection
        user={mockUser}
        lastProgress={null}
        onContinueLearning={() => {}}
      />
    )

    expect(screen.queryByText(/上次学到/)).not.toBeInTheDocument()
  })

  it('renders continue learning button', () => {
    render(<WelcomeSection user={mockUser} onContinueLearning={() => {}} />)

    expect(screen.getByText('继续学习')).toBeInTheDocument()
  })

  it('calls onContinueLearning when button is clicked', () => {
    const handleClick = jest.fn()
    render(<WelcomeSection user={mockUser} onContinueLearning={handleClick} />)

    fireEvent.click(screen.getByText('继续学习'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('displays English labels when lang is "en"', () => {
    render(<WelcomeSection user={mockUser} onContinueLearning={() => {}} lang="en" />)

    expect(screen.getByText('Continue Learning')).toBeInTheDocument()
    expect(screen.getByText(/(Good morning|Good afternoon|Good evening)/)).toBeInTheDocument()
  })

  it('displays challenge text', () => {
    render(<WelcomeSection user={mockUser} onContinueLearning={() => {}} lang="zh" />)

    expect(screen.getByText(/今天准备挑战点什么/)).toBeInTheDocument()
  })
})
