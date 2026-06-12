'use client'

import { useAIAdminConfig } from './use-ai-admin-config'
import {
  Bot,
  Save,
  Loader2,
  CheckCircle,
  AlertCircle,
  Settings,
  Wifi,
  WifiOff,
  Cloud,
  ChevronRight,
  Zap,
  Trash2,
  Pencil,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Field } from './components/field'
import { ApiKeyField } from './components/api-key-field'
import { LocalFirstToggle } from './components/local-first-toggle'
import { ConfigCard } from './components/config-card'
import { ProviderCard } from './components/provider-card'

type TabId = 'deepseek' | 'minimax' | 'status'

const TABS: { id: TabId; label: string }[] = [
  { id: 'deepseek', label: 'DeepSeek' },
  { id: 'minimax', label: 'MiniMax' },
  { id: 'status', label: '状态' },
]

export default function AdminAISettingsPage() {
  const ctx = useAIAdminConfig()

  if (ctx.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="size-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card shadow-sm border-b">
        <div className="max-w-4xl mx-auto p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="size-6 text-primary" />
            <h1 className="text-xl font-semibold text-foreground">AI 配置管理</h1>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => ctx.push('/admin')}
          >
            返回管理后台
          </Button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Message */}
        {ctx.message && (
          <div className={cn(
            'mb-4 p-4 rounded-lg flex items-center gap-2',
            ctx.message.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
          )}>
            {ctx.message.type === 'success' ? <CheckCircle className="size-5" /> : <AlertCircle className="size-5" />}
            <span>{ctx.message.text}</span>
          </div>
        )}

        {/* Current Status Banner */}
        {ctx.config && (
          <div className="mb-6 flex items-center gap-3 p-4 bg-muted rounded-lg">
            <Bot className="size-5 text-primary" />
            <span className="text-sm font-medium">
              当前: <span className="text-primary">{ctx.config.provider}</span>
              {' / '}
              <span>{ctx.config.model}</span>
            </span>
            {ctx.config.is_local_first && (
              <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">本地优先</span>
            )}
            <span className="ml-auto text-xs text-muted-foreground">
              {ctx.config.is_configured ? '已配置' : '未配置'}
            </span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-muted p-1 rounded-lg w-fit">
          {TABS.map(tab => (
            <Button
              type="button"
              key={tab.id}
              variant="ghost"
              size="sm"
              onClick={() => {
                ctx.setActiveTab(tab.id)
                if (tab.id === 'status') ctx.fetchStatus()
              }}
              className={cn(
                'rounded-md',
                ctx.activeTab === tab.id
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {tab.label}
            </Button>
          ))}
        </div>

        {/* Tab Content */}
        {ctx.activeTab === 'deepseek' && (
          <ConfigCard
            title="DeepSeek"
            description="使用 DeepSeek GPT 系列模型"
            icon={<Cloud className="size-5" />}
            isSaving={ctx.isSaving}
            isTesting={ctx.isTesting}
            testResult={ctx.testResult}
            onSave={ctx.handleSaveDeepSeek}
            onTest={ctx.handleTestDeepSeek}
          >
            <ApiKeyField
              label="API Key"
              hasKey={ctx.hasDeepseekKey}
              preview={ctx.deepseekKeyPreview}
              keyLength={ctx.deepseekKeyLength}
              value={ctx.deepseekKey}
              onChange={ctx.setDeepseekKey}
              replaceMode={ctx.deepseekKeyReplaceMode}
              onEnterReplace={() => ctx.setDeepseekKeyReplaceMode(true)}
              onCancelReplace={() => {
                ctx.setDeepseekKeyReplaceMode(false)
                ctx.setDeepseekKey('')
              }}
              onDelete={ctx.handleDeleteDeepseekKey}
              placeholder="sk-xxxxxxxxxxxx"
            />
            <Field label="模型">
              <select
                value={ctx.deepseekModel}
                onChange={e => ctx.setDeepseekModel(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="deepseek-v4-flash">deepseek-v4-flash</option>
              </select>
            </Field>
            <Field label={`温度参数: ${ctx.deepseekTemp}`}>
              <input
                type="range" min="0" max="1" step="0.1"
                value={ctx.deepseekTemp}
                onChange={e => ctx.setDeepseekTemp(parseFloat(e.target.value))}
                aria-label="温度参数"
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>精确 (0)</span><span>创意 (1)</span>
              </div>
            </Field>
            <Field label="Base URL（可选）" hint="用于代理或兼容 DeepSeek 接口的其他服务">
              <input
                type="text"
                value={ctx.deepseekUrl}
                onChange={e => ctx.setDeepseekUrl(e.target.value)}
                placeholder="https://api.deepseek.com"
                aria-label="Base URL（可选）"
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </Field>
            <LocalFirstToggle checked={ctx.localFirst} onChange={ctx.setLocalFirst} />
          </ConfigCard>
        )}

        {ctx.activeTab === 'minimax' && (
          <ConfigCard
            title="MiniMax"
            description="使用 MiniMax-M2.7 模型（Anthropic Claude 兼容格式）"
            icon={<Bot className="size-5" />}
            isSaving={ctx.isSaving}
            isTesting={ctx.isTesting}
            testResult={ctx.testResult}
            onSave={ctx.handleSaveMinimax}
            onTest={ctx.handleTestMinimax}
          >
            <ApiKeyField
              label="API Key"
              hasKey={ctx.hasMinimaxKey}
              preview={ctx.minimaxKeyPreview}
              keyLength={ctx.minimaxKeyLength}
              value={ctx.minimaxKey}
              onChange={ctx.setMinimaxKey}
              replaceMode={ctx.minimaxKeyReplaceMode}
              onEnterReplace={() => ctx.setMinimaxKeyReplaceMode(true)}
              onCancelReplace={() => {
                ctx.setMinimaxKeyReplaceMode(false)
                ctx.setMinimaxKey('')
              }}
              onDelete={ctx.handleDeleteMinimaxKey}
              placeholder="sk-cp-xxxxxxxxxxxx"
            />
            <Field label="Base URL">
              <input
                type="text"
                value={ctx.minimaxUrl}
                onChange={e => ctx.setMinimaxUrl(e.target.value)}
                placeholder="https://api.minimaxi.com/anthropic"
                aria-label="Base URL"
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </Field>
            <Field label="模型">
              <select
                value={ctx.minimaxModel}
                onChange={e => ctx.setMinimaxModel(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="MiniMax-M2.7">MiniMax-M2.7</option>
                <option value="MiniMax-M2">MiniMax-M2</option>
                <option value="abab6.5s-chat">abab6.5s-chat</option>
                <option value="abab6-chat">abab6-chat</option>
              </select>
            </Field>
            <Field label={`温度参数: ${ctx.minimaxTemp}`}>
              <input
                type="range" min="0" max="1" step="0.1"
                value={ctx.minimaxTemp}
                onChange={e => ctx.setMinimaxTemp(parseFloat(e.target.value))}
                aria-label="温度参数"
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>精确 (0)</span><span>创意 (1)</span>
              </div>
            </Field>
            <LocalFirstToggle checked={ctx.localFirst} onChange={ctx.setLocalFirst} />
          </ConfigCard>
        )}

        {ctx.activeTab === 'status' && (
          <div className="flex flex-col gap-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">连接状态</h2>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={ctx.fetchStatus}
                disabled={ctx.isRefreshing}
                className="text-primary hover:text-primary/80"
              >
                <ChevronRight className={cn('size-4 mr-1', ctx.isRefreshing && 'animate-spin')} />
                刷新
              </Button>
            </div>
            {ctx.isRefreshing && !ctx.status ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="size-6 animate-spin text-primary" />
              </div>
            ) : ctx.status ? (
              <>
                <div className="p-4 bg-muted rounded-lg">
                  <div className="text-sm font-medium mb-2">当前激活</div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold">{ctx.status.current_provider}</span>
                    <span className="text-muted-foreground">/</span>
                    <span>{ctx.status.current_model}</span>
                    {ctx.status.is_local_first && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">本地优先</span>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {ctx.status.providers.map(p => (
                    <ProviderCard key={p.type} provider={p} />
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                加载状态信息...
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

