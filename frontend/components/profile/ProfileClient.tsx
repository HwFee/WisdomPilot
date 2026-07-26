'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'
import { getProfile } from '@/lib/api/deck/profile'
import type { ProfileData } from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { PanelTag } from '../deck/kit'

const TABS = [
  { key: 'overview', label: '概览' },
  { key: 'cores', label: '智核流水' },
  { key: 'arena', label: '竞技场' },
  { key: 'certs', label: '认证' },
  { key: 'leaderboard', label: '排行榜' },
] as const

type TabKey = (typeof TABS)[number]['key']

/* ── 各 tab 内容 ── */

function OverviewTab({ data }: { data: ProfileData }) {
  const summary = [
    { k: '竞技场段位', v: data.arena.tier },
    { k: '本周排名', v: `#${data.arena.week_rank}` },
    { k: '已认证', v: `${data.certifications.length} 项` },
    { k: '智核余额', v: String(data.cores.balance) },
  ]
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {summary.map((s) => (
          <div key={s.k} className="deck-panel p-4">
            <div className="font-mono text-[10px] tracking-[1.5px] text-faint">{s.k}</div>
            <div className="mt-1.5 font-mono text-lg text-signal">{s.v}</div>
          </div>
        ))}
      </div>
      <div className="deck-panel p-[18px_20px]">
        <PanelTag label="RECENT · 最近动态" />
        <div className="mt-3">
          {data.recent.map((item, i) => (
            <div key={i} className="flex gap-3 border-t border-line py-2 text-xs first:border-t-0">
              <span className="shrink-0 font-mono text-faint">{item.time}</span>
              <span className="text-dim">
                {item.segments.map((seg, j) => (
                  <span
                    key={j}
                    className={
                      seg.tone === 'strong'
                        ? 'font-medium text-text'
                        : seg.tone === 'ok'
                          ? 'text-signal'
                          : seg.tone === 'bad'
                            ? 'text-deck-red'
                            : undefined
                    }
                  >
                    {seg.t}
                  </span>
                ))}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function CoresTab({ data }: { data: ProfileData }) {
  return (
    <div className="deck-panel p-[18px_20px]">
      <PanelTag label={`CORES · 余额 ${data.cores.balance}`} variant="on" />
      <div className="mt-3">
        {data.cores.transactions.map((t, i) => (
          <div key={i} className="flex items-center gap-4 border-t border-line py-2.5 font-mono text-[11px] first:border-t-0">
            <span className="w-24 shrink-0 text-faint">{t.time}</span>
            <span className={`w-12 shrink-0 ${t.delta > 0 ? 'text-signal' : 'text-deck-red'}`}>
              {t.delta > 0 ? `+${t.delta}` : t.delta}
            </span>
            <span className="text-dim">{t.reason}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ArenaTab({ data }: { data: ProfileData }) {
  const stats = [
    { k: '积分 RATING', v: String(data.arena.rating) },
    { k: '本周排名', v: `#${data.arena.week_rank}` },
    { k: '排名变动', v: `▲ ${data.arena.rank_delta}` },
    { k: '当前连对', v: `${data.arena.win_streak} 场` },
  ]
  return (
    <div className="space-y-4">
      <div className="deck-panel p-[26px_28px] text-center">
        <PanelTag label="TIER · 当前段位" variant="on" />
        <div className="mt-3 font-mono text-[36px] font-medium text-signal">{data.arena.tier}</div>
        <div className="mt-1 font-mono text-[11px] text-faint">全站唯一排行榜 · 只认修 bug 的速度与准确率</div>
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((s) => (
          <div key={s.k} className="deck-panel p-4">
            <div className="font-mono text-[10px] tracking-[1.5px] text-faint">{s.k}</div>
            <div className="mt-1.5 font-mono text-lg text-text">{s.v}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function CertsTab({ data }: { data: ProfileData }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {data.certifications.map((c) => (
        <div key={c.verify_code} className="deck-panel deck-panel-hoverable p-[18px_20px]">
          <div className="flex items-baseline justify-between">
            <span className="text-[15px] font-semibold">{c.topic}</span>
            <span className="font-mono text-xs text-signal">{c.level}</span>
          </div>
          <div className="mt-2 font-mono text-[11px] text-dim">
            {c.score} 分 · {c.date}
          </div>
          <div className="mt-1.5 font-mono text-[10px] text-faint">VERIFY: {c.verify_code}</div>
        </div>
      ))}
    </div>
  )
}

function LeaderboardTab({ data }: { data: ProfileData }) {
  const top = data.leaderboard.filter((e) => !e.is_self)
  const self = data.leaderboard.find((e) => e.is_self)
  return (
    <div className="deck-panel p-[18px_20px]">
      <PanelTag label="LEADERBOARD · 调试竞技场本周排行" />
      <div className="mt-3">
        {top.map((e) => (
          <div key={e.rank} className="flex items-center gap-3 border-t border-line py-2 font-mono text-[11px] text-dim first:border-t-0">
            <span className="w-8 text-faint">#{e.rank}</span>
            <span className="text-text">{e.name}</span>
            <span className="ml-auto">{e.rating}</span>
            <span className="w-10 text-right text-faint">+{e.solved_today}</span>
          </div>
        ))}
      </div>
      {self && (
        <div className="mt-2 border-t border-line-bright pt-2">
          <div className="flex items-center gap-3 py-2 font-mono text-[11px] text-signal">
            <span className="w-8">#{self.rank}</span>
            <span>{self.name}（你）</span>
            <span className="ml-auto">{self.rating}</span>
            <span className="w-10 text-right">+{self.solved_today}</span>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── 主组件 ── */

export function ProfileClient() {
  const { push } = useRouter()
  const [data, setData] = useState<ProfileData | null>(null)
  const [tab, setTab] = useState<TabKey>('overview')

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    getProfile().then(setData)
  }, [push])

  return (
    <DeckShell>
      {!data ? (
        <div className="deck-panel p-8 font-mono text-sm text-dim">
          载入档案<span className="deck-cursor ml-2" />
        </div>
      ) : (
        <>
          {/* 身份卡 */}
          <div className="deck-panel deck-boot deck-boot-1 flex flex-wrap items-center gap-x-8 gap-y-2 p-[22px_24px]">
            <div>
              <PanelTag label="PROFILE · 档案" variant="on" />
              <div className="mt-2 text-xl font-semibold">{data.user.name}</div>
            </div>
            <span className="font-mono text-[11px] text-dim">
              加入 <b className="font-medium text-text">{data.user.joined_days}</b> 天
            </span>
            <span className="font-mono text-[11px] text-dim">
              段位 <b className="font-medium text-signal">{data.arena.tier}</b>
            </span>
            <span className="font-mono text-[11px] text-dim">
              ◈ 智核 <b className="font-medium text-text">{data.cores.balance}</b>
            </span>
          </div>

          {/* tab 栏 */}
          <div className="deck-boot deck-boot-2 mt-6 flex gap-1 border-b border-line">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`-mb-px border-b-2 px-4 py-2.5 font-mono text-xs transition-colors ${
                  tab === t.key
                    ? 'border-signal text-signal'
                    : 'border-transparent text-dim hover:text-text'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="deck-boot deck-boot-2 mt-5">
            {tab === 'overview' && <OverviewTab data={data} />}
            {tab === 'cores' && <CoresTab data={data} />}
            {tab === 'arena' && <ArenaTab data={data} />}
            {tab === 'certs' && <CertsTab data={data} />}
            {tab === 'leaderboard' && <LeaderboardTab data={data} />}
          </div>
        </>
      )}
    </DeckShell>
  )
}
