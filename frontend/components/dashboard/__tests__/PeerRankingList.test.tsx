/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { PeerRankingList } from '../PeerRankingList'

describe('PeerRankingList', () => {
  const mockCurrentUser = {
    userId: 'user-1',
    username: 'CurrentUser',
    rank: 5,
  }

  const mockPeers = [
    { userId: 'user-2', username: 'Alice', rank: 1, xp: 1000 },
    { userId: 'user-3', username: 'Bob', rank: 2, xp: 800 },
    { userId: 'user-4', username: 'Charlie', rank: 3, xp: 600 },
    { userId: 'user-5', username: 'Diana', rank: 4, xp: 400 },
  ]

  it('renders all peers', () => {
    render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={mockPeers}
      />
    )

    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
    expect(screen.getByText('Charlie')).toBeInTheDocument()
    expect(screen.getByText('Diana')).toBeInTheDocument()
  })

  it('highlights current user', () => {
    render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={mockPeers}
        lang="zh"
      />
    )

    expect(screen.getByText('CurrentUser')).toBeInTheDocument()
    expect(screen.getByText('(你)')).toBeInTheDocument()
  })

  it('displays ranks correctly', () => {
    render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={mockPeers}
        lang="zh"
      />
    )

    // Check rank numbers are displayed
    expect(screen.getAllByText('1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('2').length).toBeGreaterThan(0)
  })

  it('sorts peers by rank', () => {
    const unsortedPeers = [
      { userId: 'user-3', username: 'Bob', rank: 2 },
      { userId: 'user-2', username: 'Alice', rank: 1 },
    ]

    const { container } = render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={unsortedPeers}
      />
    )

    const peerNames = container.querySelectorAll('.text-foreground')
    const names = Array.from(peerNames).map(el => el.textContent)

    // Alice (rank 1) should come before Bob (rank 2)
    const aliceIndex = names.findIndex(n => n?.includes('Alice'))
    const bobIndex = names.findIndex(n => n?.includes('Bob'))
    expect(aliceIndex).toBeLessThan(bobIndex)
  })

  it('shows empty state when no peers', () => {
    render(
      <PeerRankingList
        currentUser={{ userId: 'user-1', username: 'Test', rank: 0 }}
        peers={[]}
        lang="zh"
      />
    )

    expect(screen.getByText('开始学习以加入排行榜')).toBeInTheDocument()
  })

  it('calls onViewAll when button clicked', () => {
    const handleViewAll = jest.fn()
    render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={mockPeers}
        onViewAll={handleViewAll}
        lang="zh"
      />
    )

    fireEvent.click(screen.getByText('查看完整排行榜'))
    expect(handleViewAll).toHaveBeenCalledTimes(1)
  })

  it('displays English labels when lang is "en"', () => {
    render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={mockPeers}
        lang="en"
      />
    )

    expect(screen.getByText('Peer Ranking')).toBeInTheDocument()
    expect(screen.getByText('(You)')).toBeInTheDocument()
  })

  it('applies compact mode', () => {
    const { container } = render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={mockPeers}
        compact={true}
      />
    )

    expect(container.querySelector('.overflow-hidden')).toBeInTheDocument()
  })

  it('shows level indicator text', () => {
    render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={mockPeers}
        lang="zh"
      />
    )

    expect(screen.getByText('显示与你同级别的学习者')).toBeInTheDocument()
  })

  it('filters out current user from peers list', () => {
    const peersWithCurrentUser = [
      ...mockPeers,
      { userId: 'user-1', username: 'CurrentUser', rank: 5 },
    ]

    render(
      <PeerRankingList
        currentUser={mockCurrentUser}
        peers={peersWithCurrentUser}
      />
    )

    // Current user should only appear once (in the highlighted section)
    const currentUserElements = screen.getAllByText('CurrentUser')
    expect(currentUserElements.length).toBe(1)
  })
})
