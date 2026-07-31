'use client'

import { useEffect, useState } from 'react'

/** localStorage 引导标记 key：'1' = 已看过（不再展示） */
export const GUIDE_STORAGE_KEY = 'deck-guide-seen'

/** 首访判定：未见过返回 true（展示引导）；storage 抛异常时 fail-open 仍展示 */
export function shouldShowGuide(storage: Pick<Storage, 'getItem'>): boolean {
  try {
    return storage.getItem(GUIDE_STORAGE_KEY) !== '1'
  } catch {
    return true
  }
}

/** 写入已看过标记；写失败不阻塞（下次仍会展示） */
export function markGuideSeen(storage: Pick<Storage, 'setItem'>): void {
  try {
    storage.setItem(GUIDE_STORAGE_KEY, '1')
  } catch {
    /* 忽略：引导状态是纯本地优化，写失败不致命 */
  }
}

const GUIDE_STEPS = [
  {
    title: '三轴能力模型',
    body: '审阅、调试、实现 —— 所有训练都会沉淀到这三根能力轴上，图谱实时反映你的进度。',
  },
  {
    title: '掌握度与 HLR',
    body: '系统按你的答题记录估算记忆强度，快忘的知识点会自动安排复习。',
  },
  {
    title: '智核',
    body: '提问导师要消耗智核；每日登录补充，通过认证可以赚取。',
  },
  {
    title: '四个训练模块',
    body: '审查室练挑错、竞技场练修 bug、导师负责追问与费曼检验、认证证明不靠 AI 的基本功。',
  },
] as const

/** 首访引导：4 屏分步卡，完成或跳过即记住，不再展示。 */
export function FirstRunGuide() {
  const [show, setShow] = useState(false)
  const [step, setStep] = useState(0)

  // 挂载时读一次 localStorage 决定显隐（渲染期不稳定的值不参与 render）
  useEffect(() => {
    setShow(shouldShowGuide(window.localStorage))
  }, [])

  if (!show) return null

  const close = () => {
    markGuideSeen(window.localStorage)
    setShow(false)
  }
  const current = GUIDE_STEPS[step]
  const isLast = step === GUIDE_STEPS.length - 1

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="新手引导"
    >
      <div className="deck-panel w-[min(92vw,440px)] p-6">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] tracking-[1.5px] text-faint">
            FIRST RUN · 新手引导
          </span>
          <span className="font-mono text-[10px] text-faint">
            {step + 1} / {GUIDE_STEPS.length}
          </span>
        </div>
        <h2 className="mt-3 text-base font-semibold text-text">{current.title}</h2>
        <p className="mt-2 text-[13px] leading-relaxed text-dim">{current.body}</p>
        <div className="mt-5 flex items-center justify-between gap-3">
          <button type="button" onClick={close} className="deck-btn-ghost !px-3 !py-1.5 text-[11px]">
            跳过
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              disabled={step === 0}
              className="deck-btn-ghost !px-3 !py-1.5 text-[11px] disabled:opacity-40"
            >
              上一步
            </button>
            {isLast ? (
              <button type="button" onClick={close} className="deck-btn-primary !px-4 !py-1.5 text-xs">
                完成并记住
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                className="deck-btn-primary !px-4 !py-1.5 text-xs"
              >
                下一步
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
