/**
 * 首访引导测试：shouldShowGuide 三分支（未见/已见/异常 fail-open）、
 * markGuideSeen 写入、组件分屏与「跳过/完成并记住」落标记。
 */
import { fireEvent, render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import {
  GUIDE_STORAGE_KEY,
  FirstRunGuide,
  markGuideSeen,
  shouldShowGuide,
} from '@/components/deck/FirstRunGuide'

describe('shouldShowGuide', () => {
  it('未见过返回 true', () => {
    expect(shouldShowGuide({ getItem: () => null })).toBe(true)
  })

  it('已标记为 1 返回 false', () => {
    expect(shouldShowGuide({ getItem: () => '1' })).toBe(false)
  })

  it('storage 抛异常时 fail-open 返回 true', () => {
    const throwing = {
      getItem: () => {
        throw new Error('storage denied')
      },
    }
    expect(shouldShowGuide(throwing)).toBe(true)
  })
})

describe('markGuideSeen', () => {
  it('写入 deck-guide-seen = 1', () => {
    const setItem = jest.fn()
    markGuideSeen({ setItem })
    expect(setItem).toHaveBeenCalledWith(GUIDE_STORAGE_KEY, '1')
  })
})

describe('FirstRunGuide 组件', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('未见过时展示第一屏', () => {
    render(<FirstRunGuide />)
    expect(screen.getByText('三轴能力模型')).toBeInTheDocument()
  })

  it('已见过时不渲染', () => {
    window.localStorage.setItem(GUIDE_STORAGE_KEY, '1')
    render(<FirstRunGuide />)
    expect(screen.queryByText('三轴能力模型')).not.toBeInTheDocument()
  })

  it('下一步切屏，跳过写入标记并关闭', () => {
    render(<FirstRunGuide />)
    fireEvent.click(screen.getByText('下一步'))
    expect(screen.getByText('掌握度与 HLR')).toBeInTheDocument()

    fireEvent.click(screen.getByText('跳过'))
    expect(window.localStorage.getItem(GUIDE_STORAGE_KEY)).toBe('1')
    expect(screen.queryByText('掌握度与 HLR')).not.toBeInTheDocument()
  })

  it('末屏显示「完成并记住」，点击写入标记并关闭', () => {
    render(<FirstRunGuide />)
    fireEvent.click(screen.getByText('下一步'))
    fireEvent.click(screen.getByText('下一步'))
    fireEvent.click(screen.getByText('下一步'))
    expect(screen.getByText('四个训练模块')).toBeInTheDocument()

    fireEvent.click(screen.getByText('完成并记住'))
    expect(window.localStorage.getItem(GUIDE_STORAGE_KEY)).toBe('1')
    expect(screen.queryByText('四个训练模块')).not.toBeInTheDocument()
  })
})
