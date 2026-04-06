'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getAIConfig, updateAIConfig, AIConfigResponse, UpdateAIConfigRequest } from '@/lib/ai-api'
import { Bot, Save, Loader2, CheckCircle, AlertCircle, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function AdminAISettingsPage() {
  const router = useRouter()
  const [config, setConfig] = useState<AIConfigResponse | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('gpt-4o-mini')
  const [provider, setProvider] = useState('openai')
  const [temperature, setTemperature] = useState(0.7)
  const [baseUrl, setBaseUrl] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  const currentUser = typeof window !== 'undefined'
    ? JSON.parse(localStorage.getItem('user') || 'null')
    : null

  useEffect(() => {
    if (!token || !currentUser?.is_admin) {
      router.push('/login')
      return
    }
    fetchConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchConfig = async () => {
    try {
      setIsLoading(true)
      const data = await getAIConfig(token!)
      setConfig(data)
      setProvider(data.provider)
      setModel(data.model)
      setTemperature(data.temperature)
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : '获取配置失败' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    if (!token) return

    setIsSaving(true)
    setMessage(null)

    try {
      const request: UpdateAIConfigRequest = {
        provider,
        model,
        temperature,
      }

      if (apiKey.trim()) {
        request.api_key = apiKey.trim()
      }

      if (baseUrl.trim()) {
        request.base_url = baseUrl.trim()
      }

      await updateAIConfig(token, request)
      setMessage({ type: 'success', text: 'AI 配置已保存' })
      fetchConfig()
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : '保存失败' })
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-primary" />
            <h1 className="text-xl font-bold text-foreground">AI 配置管理</h1>
          </div>
          <button
            onClick={() => router.push('/admin')}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            返回管理后台
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {message && (
          <div className={cn(
            'mb-4 p-4 rounded-lg flex items-center gap-2',
            message.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
          )}>
            {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            <span>{message.text}</span>
          </div>
        )}

        <div className="bg-card rounded-lg shadow p-6 space-y-6">
          {/* 状态指示 */}
          <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
            <Bot className={cn(
              'w-5 h-5',
              config?.is_configured ? 'text-emerald-600' : 'text-muted-foreground'
            )} />
            <span className="text-sm font-medium">
              {config?.is_configured ? 'AI 服务已配置' : 'AI 服务未配置'}
            </span>
            {config && (
              <span className="text-xs text-muted-foreground ml-auto">
                {config.provider} / {config.model}
              </span>
            )}
          </div>

          {/* API 提供商 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">AI 提供商</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
            >
              <option value="openai">OpenAI</option>
              <option value="local">本地模型（开发中）</option>
            </select>
          </div>

          {/* API Key */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">API 密钥</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-xxxxxxxxxxxx"
              className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
            />
            <p className="text-xs text-muted-foreground">留空则使用现有配置</p>
          </div>

          {/* 模型 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">模型</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
            >
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>

          {/* 温度 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              温度参数: {temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>精确 (0)</span>
              <span>创意 (1)</span>
            </div>
          </div>

          {/* Base URL */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Base URL（可选）</label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.openai.com/v1"
              className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
            />
            <p className="text-xs text-muted-foreground">用于代理或兼容 OpenAI 接口的其他服务</p>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {isSaving ? '保存中...' : '保存配置'}
          </button>
        </div>
      </main>
    </div>
  )
}
