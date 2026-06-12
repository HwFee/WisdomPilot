'use client'

import { CheckCircle, XCircle, Clock, Cpu, AlertTriangle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TestCaseResult {
  passed: boolean
  input: string
  expected: string
  actual: string
  time?: number
  memory?: number
  status?: 'AC' | 'WA' | 'TLE' | 'MLE' | 'RE' | 'CE'
  message?: string
}

interface LuoguTestCaseTableProps {
  results: TestCaseResult[]
  passedCount: number
  totalCount: number
  isRunning?: boolean
}

const STATUS_CONFIG: Record<string, { className: string; icon: typeof XCircle; label: string }> = {
  WA: { className: 'inline-flex items-center px-3 py-1 bg-destructive/10 text-destructive rounded font-semibold text-xs', icon: XCircle, label: 'WA' },
  TLE: { className: 'inline-flex items-center px-3 py-1 bg-warning/10 text-warning rounded font-semibold text-xs', icon: Clock, label: 'TLE' },
  MLE: { className: 'inline-flex items-center px-3 py-1 bg-warning/10 text-warning rounded font-semibold text-xs', icon: Cpu, label: 'MLE' },
  RE: { className: 'inline-flex items-center px-3 py-1 bg-primary/10 text-primary rounded font-semibold text-xs', icon: AlertTriangle, label: 'RE' },
  CE: { className: 'inline-flex items-center px-3 py-1 bg-destructive/10 text-destructive rounded font-semibold text-xs', icon: XCircle, label: 'CE' },
}

function formatMemory(memory?: number) {
  if (!memory) return '-'
  return `${(memory / 1024).toFixed(2)} MB`
}

function formatTime(time?: number) {
  if (!time) return '-'
  return `${time} ms`
}

export function LuoguTestCaseTable({
  results,
  passedCount,
  totalCount,
  isRunning = false,
}: LuoguTestCaseTableProps) {
  const allPassed = passedCount === totalCount && totalCount > 0

  return (
    <div className="w-full">
      {/* 总体状态栏 */}
      <div
        className={cn(
          'flex items-center justify-between px-5 py-4 border border-border rounded-t-lg border-b',
          allPassed
            ? 'bg-success/5 border-success/30'
            : passedCount > 0
            ? 'bg-card'
            : 'bg-destructive/5 border-destructive/30'
        )}
      >
        <div className="flex items-center gap-2">
          {isRunning ? (
            <>
              <Loader2 className="size-5 text-primary animate-spin" />
              <span className="font-semibold text-primary">评测中...</span>
            </>
          ) : allPassed ? (
            <>
              <CheckCircle className="size-5 text-success" />
              <span className="font-semibold text-success">通过</span>
            </>
          ) : (
            <>
              <XCircle className="size-5 text-destructive" />
              <span className="font-semibold text-destructive">未通过</span>
            </>
          )}
        </div>
        <span className="text-sm text-muted-foreground">
          通过 {passedCount}/{totalCount} 个测试点
        </span>
      </div>

      {/* 测试点表格 */}
      <table className="w-full border border-t-0 border-border rounded-b-lg overflow-hidden border-collapse">
        <thead className="bg-muted">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider" style={{ width: 80 }}>
              测试点
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider" style={{ width: 100 }}>
              状态
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider" style={{ width: 100 }}>
              用时
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider" style={{ width: 120 }}>
              内存
            </th>
          </tr>
        </thead>
        <tbody>
          {results.map((result, index) => (
            <tr
              key={`case-${result.input.slice(0, 30)}`}
              className={cn(
                'border-b border-border last:border-b-0 hover:bg-muted/50 transition-colors',
                result.passed ? 'bg-success/[0.02]' : 'bg-destructive/[0.02]'
              )}
            >
              <td className="px-4 py-3 font-medium text-foreground">#{index + 1}</td>
              <td className="px-4 py-3">
                <StatusBadge result={result} index={index} isRunning={isRunning} />
              </td>
              <td className="px-4 py-3 text-muted-foreground font-mono text-sm">
                {formatTime(result.time)}
              </td>
              <td className="px-4 py-3 text-muted-foreground font-mono text-sm">
                {formatMemory(result.memory)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface StatusBadgeProps {
  result: TestCaseResult
  index: number
  isRunning: boolean
}

function StatusBadge({ result, index, isRunning }: StatusBadgeProps) {
  if (isRunning && index >= 0) {
    return (
      <span className="inline-flex items-center px-3 py-1 bg-muted text-muted-foreground rounded font-semibold text-xs">
        <Loader2 className="size-3.5 mr-1 animate-spin" />
        评测中
      </span>
    )
  }

  if (result.passed) {
    return (
      <span className="inline-flex items-center px-3 py-1 bg-success/10 text-success rounded font-semibold text-xs">
        <CheckCircle className="size-3.5 mr-1" />
        AC
      </span>
    )
  }

  const status = result.status || 'WA'
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.WA
  const Icon = config.icon

  return (
    <span className={config.className}>
      <Icon className="size-3.5 mr-1" />
      {config.label}
    </span>
  )
}

/* 简洁版测试点摘要 */
interface TestCasesSummaryProps {
  passedCount: number
  totalCount: number
}

export function LuoguTestCasesSummary({ passedCount, totalCount }: TestCasesSummaryProps) {
  const percentage = totalCount > 0 ? Math.round((passedCount / totalCount) * 100) : 0
  const allPassed = passedCount === totalCount && totalCount > 0

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-muted rounded-lg">
      <div className="flex items-center gap-2">
        <div className={cn('size-2 rounded-full', allPassed ? 'bg-success' : 'bg-destructive')} />
        <span className="text-sm font-medium text-foreground">
          {passedCount}/{totalCount}
        </span>
      </div>
      <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
        <div
          className="h-full bg-success rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
