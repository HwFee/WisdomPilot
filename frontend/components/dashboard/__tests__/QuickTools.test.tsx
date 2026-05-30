/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { QuickTools } from '../QuickTools'

describe('QuickTools', () => {
  it('renders all 4 tool cards', () => {
    render(<QuickTools />)

    expect(screen.getByText('错题本')).toBeInTheDocument()
    expect(screen.getByText('收藏夹')).toBeInTheDocument()
    expect(screen.getByText('笔记')).toBeInTheDocument()
    // 打卡模块包含日期
    expect(screen.getByText('打卡')).toBeInTheDocument()
  })

  it('displays wrong count when provided', () => {
    render(<QuickTools wrongCount={12} />)

    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('displays streak days', () => {
    render(<QuickTools streakDays={7} />)

    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('calls onWrongClick when wrong questions card is clicked', () => {
    const handleClick = jest.fn()
    render(<QuickTools wrongCount={5} onWrongClick={handleClick} />)

    fireEvent.click(screen.getByText('错题本').closest('button')!)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('calls onFavoritesClick when favorites card is clicked', () => {
    const handleClick = jest.fn()
    render(<QuickTools onFavoritesClick={handleClick} />)

    fireEvent.click(screen.getByText('收藏夹').closest('button')!)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('calls onNotesClick when notes card is clicked', () => {
    const handleClick = jest.fn()
    render(<QuickTools onNotesClick={handleClick} />)

    fireEvent.click(screen.getByText('笔记').closest('button')!)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('calls onCheckIn when check-in button is clicked', () => {
    const handleCheckIn = jest.fn()
    render(<QuickTools streakDays={0} onCheckIn={handleCheckIn} />)

    fireEvent.click(screen.getByText('打卡'))
    expect(handleCheckIn).toHaveBeenCalledTimes(1)
  })

  it('shows "已打卡" when already checked in', () => {
    render(<QuickTools streakDays={7} isCheckedIn={true} />)

    expect(screen.getByText('已打卡')).toBeInTheDocument()
    expect(screen.queryByText('打卡')).not.toBeInTheDocument()
  })

  it('displays English labels when lang is "en"', () => {
    render(<QuickTools lang="en" />)

    expect(screen.getByText('Wrong')).toBeInTheDocument()
    expect(screen.getByText('Favorites')).toBeInTheDocument()
    expect(screen.getByText('Notes')).toBeInTheDocument()
  })

  it('renders 4 cards in grid layout', () => {
    const { container } = render(<QuickTools />)
    const grid = container.querySelector('.grid-cols-4')
    expect(grid).toBeInTheDocument()
  })
})
