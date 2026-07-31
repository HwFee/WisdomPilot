'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'
import { getDeckDashboard } from '@/lib/api/deck/dashboard'
import type { DeckDashboard } from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { PanelTag, StatusBar } from '../deck/kit'
import { FirstRunGuide } from '../deck/FirstRunGuide'
import { AbilityProfile } from './AbilityProfile'
import { IntelPanels } from './IntelPanels'
import { MissionHero, PlacementHero } from './MissionHero'
import { MODULES, ModuleGrid } from './ModuleGrid'

/** 加载态：控制台风格占位 */
function DashboardLoading() {
  return (
    <div className="deck-panel p-[34px_38px]">
      <PanelTag label="SIGNAL · 信号接入中" variant="on" />
      <div className="mt-4 font-mono text-sm text-dim">
        正在同步训练数据<span className="deck-cursor ml-2" />
      </div>
    </div>
  )
}

/** 错误态：面板级降级，不白屏 */
function DashboardError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="deck-panel p-[34px_38px]">
      <PanelTag label="SIGNAL LOST · 信号中断" variant="warn" />
      <div className="mt-4 text-sm text-dim">训练数据同步失败，请检查连接后重试。</div>
      <button className="deck-btn-ghost mt-4" onClick={onRetry}>
        重新连接
      </button>
    </div>
  )
}

/** 训练舱首页：auth 守卫 + 数据加载 + 键盘 1-4 快速进入模块 */
export function DashboardClient() {
  const { push } = useRouter()
  const [data, setData] = useState<DeckDashboard | null>(null)
  const [error, setError] = useState(false)
  const [retryFlag, setRetryFlag] = useState(0)

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    let alive = true
    getDeckDashboard()
      .then((d) => alive && setData(d))
      .catch(() => alive && setError(true))
    return () => {
      alive = false
    }
  }, [push, retryFlag])

  // 键盘 1-4 快速进入模块（输入框聚焦时忽略）
  useEffect(() => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return
      const mod = MODULES.find((m) => m.hotkey === e.key)
      if (!mod) return
      const el = document.getElementById(`module-${mod.hotkey}`)
      if (el) {
        el.classList.remove('deck-flash')
        void el.offsetWidth // 重启动画
        el.classList.add('deck-flash')
        el.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'nearest' })
      }
      push(mod.href)
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [push])

  return (
    <DeckShell>
      <FirstRunGuide />
      {error ? (
        <DashboardError onRetry={() => { setError(false); setData(null); setRetryFlag((f) => f + 1) }} />
      ) : !data ? (
        <DashboardLoading />
      ) : (
        <>
          {data.main_task ? <MissionHero task={data.main_task} /> : <PlacementHero />}
          <AbilityProfile
            axes={data.ability_map.axes}
            hasPlacement={data.ability_map.has_placement}
          />
          <ModuleGrid stats={data.modules} />
          <IntelPanels
            weakPoints={data.weak_points}
            rhythmDays={data.rhythm.days}
            streakDays={data.rhythm.streak_days}
            reviewDue={data.review_due}
            feed={data.feed}
          />
          <div className="deck-boot deck-boot-4">
            <StatusBar />
          </div>
        </>
      )}
    </DeckShell>
  )
}
