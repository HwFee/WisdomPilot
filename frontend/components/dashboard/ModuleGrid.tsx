'use client'

import { useRouter } from 'next/navigation'
import type { ModuleKey, ModuleStat } from '@/lib/api/deck/types'
import { Kbd, SectionHead } from '../deck/kit'

export interface ModuleMeta {
  key: ModuleKey
  hotkey: string
  title: string
  en: string
  desc: string
  href: string
}

export const MODULES: ModuleMeta[] = [
  {
    key: 'review-gym',
    hotkey: '1',
    title: '代码审查室',
    en: 'Review Gym',
    desc: 'AI 生成的代码里被注入了缺陷，像 code review 一样把它们全部揪出来。',
    href: '/review-gym',
  },
  {
    key: 'arena',
    hotkey: '2',
    title: '调试竞技场',
    en: 'Debug Arena',
    desc: '测试全挂的程序 + 失败输出，限时修复。唯一的排行榜，只认修 bug 的速度与准确率。',
    href: '/arena',
  },
  {
    key: 'tutor',
    hotkey: '3',
    title: '苏格拉底导师',
    en: 'AI Tutor',
    desc: '不给你答案的 AI。它只会追问，直到你自己把问题想明白。每次对话消耗智核。',
    href: '/tutor',
  },
  {
    key: 'certification',
    hotkey: '4',
    title: '基本功认证',
    en: 'No-AI Zone',
    desc: '关闭一切辅助的限时手写测试。通过后获得可分享的能力凭证——证明你不靠 AI 也会。',
    href: '/certification',
  },
]

function StatItems({ stat }: { stat: ModuleStat | undefined }) {
  if (!stat) return null
  return (
    <>
      {stat.stats.map((s, i) =>
        s.trend ? (
          <span key={i} className="text-signal">
            {s.trend === 'up' ? '▲' : '▼'} {s.label}
          </span>
        ) : (
          <span key={i}>
            {s.label} <b className="font-medium text-text">{s.value}</b>
          </span>
        )
      )}
    </>
  )
}

/** 训练模块四卡：点击或按 1-4 进入 */
export function ModuleGrid({ stats }: { stats: ModuleStat[] }) {
  const { push } = useRouter()
  return (
    <>
      <div className="deck-boot deck-boot-3">
        <SectionHead
          title="训练模块 / Modules"
          note={
            <>
              按 <Kbd>1</Kbd>–<Kbd>4</Kbd> 快速进入
            </>
          }
        />
      </div>
      <section className="deck-boot deck-boot-3 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {MODULES.map((mod) => (
          <div
            key={mod.key}
            id={`module-${mod.hotkey}`}
            data-key={mod.hotkey}
            role="link"
            tabIndex={0}
            onClick={() => push(mod.href)}
            onKeyDown={(e) => e.key === 'Enter' && push(mod.href)}
            className="deck-panel deck-panel-hoverable grid cursor-pointer grid-cols-[1fr_auto] gap-x-5 gap-y-1.5 p-[22px_24px] transition-transform duration-200 hover:-translate-y-0.5"
          >
            <div className="flex items-center gap-2.5 text-base font-semibold">
              {mod.title}
              <span className="font-mono text-[10px] uppercase tracking-[1.5px] text-faint">
                {mod.en}
              </span>
            </div>
            <span className="go row-span-2 self-center font-mono text-lg text-faint transition-all duration-200">
              →
            </span>
            <div className="text-[13px] text-dim">{mod.desc}</div>
            <div className="col-span-full mt-2 flex items-center gap-[18px] border-t border-line pt-3 font-mono text-[11px] text-dim">
              <StatItems stat={stats.find((s) => s.key === mod.key)} />
              <span className="kbd-hint ml-auto rounded border border-line px-[5px] py-0 font-mono text-[10px] text-faint">
                {mod.hotkey}
              </span>
            </div>
          </div>
        ))}
      </section>
    </>
  )
}
