/**
 * Dashboard Events - 用于页面间通信的事件系统
 */

// 事件名称常量
export const DASHBOARD_EVENTS = {
  REFRESH: 'dashboard:refresh',
  EXERCISE_COMPLETE: 'dashboard:exercise_complete',
  STAGE_COMPLETE: 'dashboard:stage_complete',
} as const

// 触发仪表盘刷新事件
export function triggerDashboardRefresh(data?: {
  exerciseId?: number
  exerciseTitle?: string
  stageId?: number
  stageName?: string
  correct?: boolean
}) {
  if (typeof window !== 'undefined') {
    const event = new CustomEvent(DASHBOARD_EVENTS.REFRESH, { detail: data })
    window.dispatchEvent(event)
    console.log('Dashboard refresh triggered:', data)
  }
}

// 触发练习完成事件
export function triggerExerciseComplete(data: {
  exerciseId: number
  exerciseTitle?: string
  correct: boolean
}) {
  if (typeof window !== 'undefined') {
    const event = new CustomEvent(DASHBOARD_EVENTS.EXERCISE_COMPLETE, { detail: data })
    window.dispatchEvent(event)
    // 同时触发刷新
    triggerDashboardRefresh(data)
  }
}

// 触发关卡完成事件
export function triggerStageComplete(data: {
  stageId: number
  stageName?: string
  passed: boolean
}) {
  if (typeof window !== 'undefined') {
    const event = new CustomEvent(DASHBOARD_EVENTS.STAGE_COMPLETE, { detail: data })
    window.dispatchEvent(event)
    // 同时触发刷新
    triggerDashboardRefresh(data)
  }
}
