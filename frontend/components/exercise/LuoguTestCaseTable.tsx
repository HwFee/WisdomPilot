'use client'

import { CheckCircle, XCircle, Clock, Cpu, AlertTriangle, Loader2 } from 'lucide-react'

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
  isRunning = false
}: LuoguTestCaseTableProps) {

  const getStatusBadge = (result: TestCaseResult, index: number) => {
    if (isRunning && index >= results.length) {
      return (
        <span className="status-pending">
          <Loader2 className="size-3.5 mr-1 animate-spin" />
          评测中
        </span>
      )
    }

    if (result.passed) {
      return (
        <span className="status-ac">
          <CheckCircle className="size-3.5 mr-1" />
          AC
        </span>
      )
    }

    const status = result.status || 'WA'
    const statusConfig: Record<string, { className: string; icon: typeof XCircle; label: string }> = {
      WA: { className: 'status-wa', icon: XCircle, label: 'WA' },
      TLE: { className: 'status-tle', icon: Clock, label: 'TLE' },
      MLE: { className: 'status-mle', icon: Cpu, label: 'MLE' },
      RE: { className: 'status-re', icon: AlertTriangle, label: 'RE' },
      CE: { className: 'status-wa', icon: XCircle, label: 'CE' },
    }

    const config = statusConfig[status] || statusConfig.WA
    const Icon = config.icon

    return (
      <span className={config.className}>
        <Icon className="size-3.5 mr-1" />
        {config.label}
      </span>
    )
  }

  const allPassed = passedCount === totalCount && totalCount > 0

  return (
    <div className="w-full">
      {/* 总体状态栏 */}
      <div className={`luogu-status-header ${allPassed ? 'accepted' : passedCount > 0 ? '' : 'wrong'}`}>
        <div className="flex items-center gap-2">
          {isRunning ? (
            <>
              <Loader2 className="size-5 text-[#3498DB] animate-spin" />
              <span className="font-semibold text-[#3498DB]">评测中...</span>
            </>
          ) : allPassed ? (
            <>
              <CheckCircle className="size-5 text-[#52C41A]" />
              <span className="font-semibold text-[#52C41A]">通过</span>
            </>
          ) : (
            <>
              <XCircle className="size-5 text-[#E74C3C]" />
              <span className="font-semibold text-[#E74C3C]">未通过</span>
            </>
          )}
        </div>
        <span className="text-sm text-[#909399]">
          通过 {passedCount}/{totalCount} 个测试点
        </span>
      </div>

      {/* 测试点表格 */}
      <table className="luogu-test-table">
        <thead>
          <tr>
            <th style={{ width: 80 }}>测试点</th>
            <th style={{ width: 100 }}>状态</th>
            <th style={{ width: 100 }}>用时</th>
            <th style={{ width: 120 }}>内存</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result, index) => (
            <tr key={`case-${result.input.slice(0, 30)}`} className={result.passed ? 'bg-[rgba(82,196,26,0.02)]' : 'bg-[rgba(231,76,60,0.02)]'}>
              <td className="font-medium text-[#303133]">#{index + 1}</td>
              <td>{getStatusBadge(result, index)}</td>
              <td className="text-[#606266] font-mono text-sm">
                {formatTime(result.time)}
              </td>
              <td className="text-[#606266] font-mono text-sm">
                {formatMemory(result.memory)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* 简洁版测试点摘要 */
interface TestCasesSummaryProps {
  passedCount: number
  totalCount: number
}

export function LuoguTestCasesSummary({ passedCount, totalCount }: TestCasesSummaryProps) {
  const percentage = totalCount > 0 ? Math.round((passedCount / totalCount) * 100) : 0

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-[#F5F7FA] rounded-lg">
      <div className="flex items-center gap-2">
        <div className={`size-2 rounded-full ${passedCount === totalCount ? 'bg-[#52C41A]' : 'bg-[#E74C3C]'}`} />
        <span className="text-sm font-medium text-[#606266]">
          {passedCount}/{totalCount}
        </span>
      </div>
      <div className="flex-1 h-1.5 bg-[#E4E7ED] rounded-full overflow-hidden">
        <div
          className="h-full bg-[#52C41A] rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
