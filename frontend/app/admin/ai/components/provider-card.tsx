'use client'

import { Wifi, WifiOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ProviderStatus } from '@/lib/ai-api'

interface ProviderCardProps {
  provider: ProviderStatus
}

export function ProviderCard({ provider }: ProviderCardProps) {
  const isConnected = provider.status === 'connected'
  const Icon = isConnected ? Wifi : WifiOff
  const iconColor = isConnected ? 'text-emerald-600' : 'text-red-500'

  return (
    <div className="bg-card rounded-lg shadow p-4 border">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={cn('size-4', iconColor)} />
          <span className="font-medium capitalize">{provider.type === 'lmstudio' ? 'LM Studio' : provider.type}</span>
        </div>
        <span className={cn(
          'text-xs px-2 py-0.5 rounded-full',
          isConnected ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
        )}>
          {isConnected ? '已连接' : '未连接'}
        </span>
      </div>
      <div className="flex flex-col gap-y-1 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <span className="font-medium text-foreground">地址:</span>
          <span>{provider.address}</span>
        </div>
        {provider.model && (
          <div className="flex items-center gap-1">
            <span className="font-medium text-foreground">模型:</span>
            <span>{provider.model}</span>
          </div>
        )}
        {provider.available_models && provider.available_models.length > 0 && (
          <div className="mt-2">
            <span className="font-medium text-foreground">可用模型:</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {provider.available_models.slice(0, 5).map(m => (
                <span key={m} className="px-1.5 py-0.5 bg-muted rounded text-xs">{m}</span>
              ))}
              {provider.available_models.length > 5 && (
                <span className="text-xs">+{provider.available_models.length - 5} more</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
