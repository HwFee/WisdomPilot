/**
 * 定级仪式页（P-03）+ 训练指纹 chip（P-11）渲染测试
 */
import { fireEvent, render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { PlacementResultView } from '@/components/certification/PlacementResultView'
import { FingerprintChip } from '@/components/certification/FingerprintChip'
import type { CertResult } from '@/lib/api/deck/types'

const push = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
}))

/** 定级结果：score 40 → placementLevels(40) = { review: 2, debug: 1, implement: 2 } */
const placementResult = (score: number): CertResult => ({
  score,
  passed: false,
  certificate: null,
  per_question: [],
  new_badges: [],
})

describe('PlacementResultView（P-03 入舱画像）', () => {
  it('展示三轴初始等级、专属路径说明与训练指纹', () => {
    render(<PlacementResultView result={placementResult(40)} />)

    // 主卡仪式文案
    expect(screen.getByText('你的专属训练路径已生成')).toBeInTheDocument()
    expect(screen.getByText(/系统基于你的定级作答数据/)).toBeInTheDocument()

    // 三轴等级：审阅 LV.2 / 调试 LV.1 / 实现 LV.2
    expect(screen.getAllByText('LV.2')).toHaveLength(2)
    expect(screen.getByText('LV.1')).toBeInTheDocument()
    // 调试是最低轴 → 补强说明；审阅/实现是最高轴 → 优势说明
    expect(screen.getByText('起点偏低，系统优先安排这一轴的基础训练')).toBeInTheDocument()
    expect(screen.getAllByText('起点最高，系统在这一轴上安排进阶任务')).toHaveLength(2)

    // 专属路径卡：基于能力数据、指向最低轴
    expect(screen.getByText(/基于你的能力数据，系统会优先安排「调试」轴的基础训练/)).toBeInTheDocument()
    expect(screen.getByText(/后续的主任务推荐、复盘队列与导师追问/)).toBeInTheDocument()

    // P-11 指纹（由三轴等级推导，R-D-I 固定顺序）
    expect(screen.getByText('训练指纹')).toBeInTheDocument()
    expect(screen.getByText('R2-D1-I2')).toBeInTheDocument()
    expect(screen.getByText('· 你的能力分布独一无二')).toBeInTheDocument()

    // 约束 3：不出现「AI 生成」类过度承诺文案
    expect(screen.queryByText(/AI/)).not.toBeInTheDocument()
  })

  it('满分 100：debug 恒低一档（LV.4），调试轴补强', () => {
    render(<PlacementResultView result={placementResult(100)} />)
    expect(screen.getAllByText('LV.5')).toHaveLength(2)
    expect(screen.getByText('LV.4')).toBeInTheDocument()
    expect(screen.getByText('R5-D4-I5')).toBeInTheDocument()
    // 调试是最低轴 → 补强说明；审阅/实现是最高轴 → 优势说明
    expect(screen.getByText('起点偏低，系统优先安排这一轴的基础训练')).toBeInTheDocument()
    expect(screen.getAllByText('起点最高，系统在这一轴上安排进阶任务')).toHaveLength(2)
    expect(screen.getByText(/基于你的能力数据，系统会优先安排「调试」轴的基础训练/)).toBeInTheDocument()
  })

  it('低分 0：三轴均 LV.1 均衡起步', () => {
    render(<PlacementResultView result={placementResult(0)} />)
    expect(screen.getAllByText('LV.1')).toHaveLength(3)
    expect(screen.getByText('R1-D1-I1')).toBeInTheDocument()
    expect(screen.getByText(/三轴均衡起步。基于你的能力数据/)).toBeInTheDocument()
  })

  it('「进入训练舱」跳转 /dashboard', () => {
    render(<PlacementResultView result={placementResult(40)} />)
    expect(screen.getByText('定级得分 40 / 100 · 定级不计通过/失败')).toBeInTheDocument()
    fireEvent.click(screen.getByText('进入训练舱 →'))
    expect(push).toHaveBeenCalledWith('/dashboard')
  })
})

describe('FingerprintChip（P-11 训练指纹）', () => {
  it('渲染短码与「独一无二」说明，不暴露具体弱点', () => {
    render(<FingerprintChip code="R3-D1-I4" />)
    expect(screen.getByText('训练指纹')).toBeInTheDocument()
    expect(screen.getByText('R3-D1-I4')).toBeInTheDocument()
    expect(screen.getByText('· 你的能力分布独一无二')).toBeInTheDocument()
  })
})
