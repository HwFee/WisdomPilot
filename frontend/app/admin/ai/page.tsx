'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  getAIConfig,
  updateAIConfig,
  getAIStatus,
  testAIConnection,
  type AIConfigResponse,
  type AIStatusResponse,
  type UpdateAIConfigRequest,
  type ProviderStatus,
  type TestConnectionResponse,
} from '@/lib/ai-api'
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
  Cpu,
  ChevronRight,
  Zap,
  Trash2,
  Pencil,
} from 'lucide-react'
import { cn } from '@/lib/utils'

type TabId = 'openai' | 'minimax' | 'local' | 'status'

const TABS: { id: TabId; label: string }[] = [
  { id: 'openai', label: 'OpenAI' },
  { id: 'minimax', label: 'MiniMax' },
  { id: 'local', label: '本地模型' },
  { id: 'status', label: '状态' },
]

export default function AdminAISettingsPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<TabId>('openai')
  const [config, setConfig] = useState<AIConfigResponse | null>(null)
  const [status, setStatus] = useState<AIStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestConnectionResponse | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // OpenAI state
  const [openaiKey, setOpenaiKey] = useState('')
  const [openaiModel, setOpenaiModel] = useState('gpt-4o-mini')
  const [openaiTemp, setOpenaiTemp] = useState(0.7)
  const [openaiUrl, setOpenaiUrl] = useState('')
  const [hasOpenaiKey, setHasOpenaiKey] = useState(false)
  const [openaiKeyPreview, setOpenaiKeyPreview] = useState('')
  const [openaiKeyLength, setOpenaiKeyLength] = useState(0)
  const [openaiKeyReplaceMode, setOpenaiKeyReplaceMode] = useState(false)

  // MiniMax state
  const [minimaxKey, setMinimaxKey] = useState('')
  const [minimaxModel, setMinimaxModel] = useState('MiniMax-M2.7')
  const [minimaxTemp, setMinimaxTemp] = useState(0.7)
  const [minimaxUrl, setMinimaxUrl] = useState('https://api.minimaxi.com/anthropic')
  const [hasMinimaxKey, setHasMinimaxKey] = useState(false)
  const [minimaxKeyPreview, setMinimaxKeyPreview] = useState('')
  const [minimaxKeyLength, setMinimaxKeyLength] = useState(0)
  const [minimaxKeyReplaceMode, setMinimaxKeyReplaceMode] = useState(false)

  // Local state
  const [localProvider, setLocalProvider] = useState<'ollama' | 'lmstudio'>('ollama')
  const [localUrl, setLocalUrl] = useState('http://localhost:11434')
  const [localModel, setLocalModel] = useState('')
  const [localTemp, setLocalTemp] = useState(0.7)
  const [localFirst, setLocalFirst] = useState(false)
  const [availableModels, setAvailableModels] = useState<string[]>([])

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
      applyConfig(data)
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : '获取配置失败' })
    } finally {
      setIsLoading(false)
    }
  }

  const fetchStatus = useCallback(async () => {
    if (!token) return
    try {
      setIsRefreshing(true)
      const data = await getAIStatus(token)
      setStatus(data)
    } catch (err) {
      console.error('[AI] 获取状态失败:', err)
    } finally {
      setIsRefreshing(false)
    }
  }, [token])

  useEffect(() => {
    if (activeTab === 'status') {
      fetchStatus()
    }
  }, [activeTab, fetchStatus])

  const applyConfig = (data: AIConfigResponse) => {
    setLocalFirst(data.is_local_first)
    setHasOpenaiKey(data.provider === 'openai' && data.has_api_key)
    setHasMinimaxKey(data.provider === 'minimax' && data.has_api_key)
    // MiniMax key — from config response
    setMinimaxKeyPreview(data.api_key_preview || '')
    setMinimaxKeyLength(data.api_key_length || 0)
    setMinimaxKeyReplaceMode(false)
    setMinimaxKey('')
    // OpenAI key — from config only when OpenAI is active provider; otherwise keep stored value
    if (data.provider === 'openai') {
      setOpenaiKeyPreview(data.has_api_key ? (data.api_key_preview || '****') : '')
      setOpenaiKeyLength(data.api_key_length || 0)
    }
    setOpenaiKeyReplaceMode(false)
    setOpenaiKey('')
    if (data.provider === 'openai') {
      setActiveTab('openai')
    } else if (data.provider === 'minimax') {
      setActiveTab('minimax')
    } else if (data.provider === 'ollama' || data.provider === 'lmstudio') {
      setActiveTab('local')
      setLocalProvider(data.provider as 'ollama' | 'lmstudio')
      setLocalUrl(data.connection_address || (data.provider === 'ollama' ? 'http://localhost:11434' : 'http://localhost:1234'))
    }
  }

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 4000)
  }

  const handleSaveOpenAI = async () => {
    if (!token) return
    setIsSaving(true)
    try {
      const req: UpdateAIConfigRequest = { provider: 'openai', temperature: openaiTemp, model: openaiModel }
      // 替换模式：输入了新密钥则更新；清空则删除
      if (openaiKeyReplaceMode) {
        req.api_key = openaiKey || ''
      } else if (openaiKey) {
        // 非替换模式但有新输入（追加情况）
        req.api_key = openaiKey
      }
      // else: 保持空字符串，且没有替换模式 → 不更新 key
      if (openaiUrl.trim()) req.base_url = openaiUrl.trim()
      req.is_local_first = localFirst
      await updateAIConfig(token, req)
      setOpenaiKey('')
      setOpenaiKeyReplaceMode(false)
      showMessage('success', 'OpenAI 配置已保存')
      fetchConfig()
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : '保存失败')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSaveMinimax = async () => {
    if (!token) return
    setIsSaving(true)
    try {
      const req: UpdateAIConfigRequest = { provider: 'minimax', temperature: minimaxTemp, model: minimaxModel }
      // 替换模式：输入了新密钥则更新；清空则删除
      if (minimaxKeyReplaceMode) {
        req.api_key = minimaxKey || ''
      } else if (minimaxKey) {
        req.api_key = minimaxKey
      }
      if (minimaxUrl.trim()) req.base_url = minimaxUrl.trim()
      req.is_local_first = localFirst
      await updateAIConfig(token, req)
      setMinimaxKey('')
      setMinimaxKeyReplaceMode(false)
      showMessage('success', 'MiniMax 配置已保存')
      fetchConfig()
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : '保存失败')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSaveLocal = async () => {
    if (!token) return
    setIsSaving(true)
    try {
      const req: UpdateAIConfigRequest = { provider: localProvider, temperature: localTemp }
      if (localModel.trim()) req.model = localModel.trim()
      if (localUrl.trim()) req.local_base_url = localUrl.trim()
      req.is_local_first = localFirst
      await updateAIConfig(token, req)
      showMessage('success', '本地模型配置已保存')
      fetchConfig()
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : '保存失败')
    } finally {
      setIsSaving(false)
    }
  }

  const handleTestOpenAI = async () => {
    if (!token) return
    setIsTesting(true)
    setTestResult(null)
    try {
      const result = await testAIConnection(token, {
        provider: 'openai',
        api_key: openaiKey || undefined,
        model: openaiModel,
        base_url: openaiUrl || undefined,
      })
      setTestResult(result)
    } catch (err) {
      setTestResult({ success: false, message: err instanceof Error ? err.message : '测试失败' })
    } finally {
      setIsTesting(false)
    }
  }

  const handleTestMinimax = async () => {
    if (!token) return
    setIsTesting(true)
    setTestResult(null)
    try {
      const result = await testAIConnection(token, {
        provider: 'minimax',
        api_key: minimaxKey || undefined,
        model: minimaxModel,
        base_url: minimaxUrl || undefined,
      })
      setTestResult(result)
    } catch (err) {
      setTestResult({ success: false, message: err instanceof Error ? err.message : '测试失败' })
    } finally {
      setIsTesting(false)
    }
  }

  const handleTestLocal = async () => {
    if (!token) return
    setIsTesting(true)
    setTestResult(null)
    try {
      const result = await testAIConnection(token, {
        provider: localProvider,
        model: localModel || undefined,
        local_base_url: localUrl || undefined,
      })
      setTestResult(result)
    } catch (err) {
      setTestResult({ success: false, message: err instanceof Error ? err.message : '测试失败' })
    } finally {
      setIsTesting(false)
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
      <header className="bg-card shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-primary" />
            <h1 className="text-xl font-bold text-foreground">AI 配置管理</h1>
          </div>
          <button type="button"
            onClick={() => router.push('/admin')}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            返回管理后台
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Message */}
        {message && (
          <div className={cn(
            'mb-4 p-4 rounded-lg flex items-center gap-2',
            message.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
          )}>
            {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            <span>{message.text}</span>
          </div>
        )}

        {/* Current Status Banner */}
        {config && (
          <div className="mb-6 flex items-center gap-3 p-4 bg-muted rounded-lg">
            <Bot className="w-5 h-5 text-primary" />
            <span className="text-sm font-medium">
              当前: <span className="text-primary">{config.provider}</span>
              {' / '}
              <span>{config.model}</span>
            </span>
            {config.is_local_first && (
              <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">本地优先</span>
            )}
            <span className="ml-auto text-xs text-muted-foreground">
              {config.is_configured ? '已配置' : '未配置'}
            </span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-muted p-1 rounded-lg w-fit">
          {TABS.map(tab => (
            <button type="button"
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-md transition-all',
                activeTab === tab.id
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'openai' && (
          <ConfigCard
            title="OpenAI"
            description="使用 OpenAI GPT 系列模型"
            icon={<Cloud className="w-5 h-5" />}
            isSaving={isSaving}
            isTesting={isTesting}
            testResult={testResult}
            onSave={handleSaveOpenAI}
            onTest={handleTestOpenAI}
          >
            <ApiKeyField
              label="API Key"
              hasKey={hasOpenaiKey}
              preview={openaiKeyPreview}
              keyLength={openaiKeyLength}
              value={openaiKey}
              onChange={setOpenaiKey}
              replaceMode={openaiKeyReplaceMode}
              onEnterReplace={() => setOpenaiKeyReplaceMode(true)}
              onCancelReplace={() => {
                setOpenaiKeyReplaceMode(false)
                setOpenaiKey('')
              }}
              onDelete={async () => {
                if (!token) return
                setIsSaving(true)
                try {
                  await updateAIConfig(token, { provider: 'openai', api_key: '' })
                  setOpenaiKeyPreview('')
                  setOpenaiKeyLength(0)
                  showMessage('success', '密钥已删除')
                  fetchConfig()
                } catch (err) {
                  showMessage('error', err instanceof Error ? err.message : '删除失败')
                } finally {
                  setIsSaving(false)
                }
              }}
              placeholder="sk-xxxxxxxxxxxx"
            />
            <Field label="模型">
              <select
                value={openaiModel}
                onChange={e => setOpenaiModel(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
            </Field>
            <Field label={`温度参数: ${openaiTemp}`}>
              <input
                type="range" min="0" max="1" step="0.1"
                value={openaiTemp}
                onChange={e => setOpenaiTemp(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>精确 (0)</span><span>创意 (1)</span>
              </div>
            </Field>
            <Field label="Base URL（可选）" hint="用于代理或兼容 OpenAI 接口的其他服务">
              <input
                type="text"
                value={openaiUrl}
                onChange={e => setOpenaiUrl(e.target.value)}
                placeholder="https://api.openai.com/v1"
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </Field>
            <LocalFirstToggle checked={localFirst} onChange={setLocalFirst} />
          </ConfigCard>
        )}

        {activeTab === 'minimax' && (
          <ConfigCard
            title="MiniMax"
            description="使用 MiniMax-M2.7 模型（Anthropic Claude 兼容格式）"
            icon={<Bot className="w-5 h-5" />}
            isSaving={isSaving}
            isTesting={isTesting}
            testResult={testResult}
            onSave={handleSaveMinimax}
            onTest={handleTestMinimax}
          >
            <ApiKeyField
              label="API Key"
              hasKey={hasMinimaxKey}
              preview={minimaxKeyPreview}
              keyLength={minimaxKeyLength}
              value={minimaxKey}
              onChange={setMinimaxKey}
              replaceMode={minimaxKeyReplaceMode}
              onEnterReplace={() => setMinimaxKeyReplaceMode(true)}
              onCancelReplace={() => {
                setMinimaxKeyReplaceMode(false)
                setMinimaxKey('')
              }}
              onDelete={async () => {
                if (!token) return
                setIsSaving(true)
                try {
                  await updateAIConfig(token, { provider: 'minimax', api_key: '' })
                  setMinimaxKeyPreview('')
                  setMinimaxKeyLength(0)
                  showMessage('success', '密钥已删除')
                  fetchConfig()
                } catch (err) {
                  showMessage('error', err instanceof Error ? err.message : '删除失败')
                } finally {
                  setIsSaving(false)
                }
              }}
              placeholder="sk-cp-xxxxxxxxxxxx"
            />
            <Field label="Base URL">
              <input
                type="text"
                value={minimaxUrl}
                onChange={e => setMinimaxUrl(e.target.value)}
                placeholder="https://api.minimaxi.com/anthropic"
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </Field>
            <Field label="模型">
              <select
                value={minimaxModel}
                onChange={e => setMinimaxModel(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="MiniMax-M2.7">MiniMax-M2.7</option>
                <option value="MiniMax-M2">MiniMax-M2</option>
                <option value="abab6.5s-chat">abab6.5s-chat</option>
                <option value="abab6-chat">abab6-chat</option>
              </select>
            </Field>
            <Field label={`温度参数: ${minimaxTemp}`}>
              <input
                type="range" min="0" max="1" step="0.1"
                value={minimaxTemp}
                onChange={e => setMinimaxTemp(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>精确 (0)</span><span>创意 (1)</span>
              </div>
            </Field>
            <LocalFirstToggle checked={localFirst} onChange={setLocalFirst} />
          </ConfigCard>
        )}

        {activeTab === 'local' && (
          <ConfigCard
            title="本地模型"
            description="使用 Ollama 或 LM Studio 运行的本地大模型"
            icon={<Cpu className="w-5 h-5" />}
            isSaving={isSaving}
            isTesting={isTesting}
            testResult={testResult}
            onSave={handleSaveLocal}
            onTest={handleTestLocal}
          >
            <Field label="本地服务类型">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setLocalProvider('ollama')
                    setLocalUrl('http://localhost:11434')
                    setAvailableModels([])
                    setLocalModel('')
                  }}
                  className={cn(
                    'flex-1 px-4 py-2 text-sm rounded-lg border transition-all',
                    localProvider === 'ollama'
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border text-muted-foreground hover:border-primary/50'
                  )}
                >
                  Ollama
                  <span className="block text-xs font-normal mt-0.5 opacity-70">端口 11434</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setLocalProvider('lmstudio')
                    setLocalUrl('http://localhost:1234')
                    setAvailableModels([])
                    setLocalModel('')
                  }}
                  className={cn(
                    'flex-1 px-4 py-2 text-sm rounded-lg border transition-all',
                    localProvider === 'lmstudio'
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border text-muted-foreground hover:border-primary/50'
                  )}
                >
                  LM Studio
                  <span className="block text-xs font-normal mt-0.5 opacity-70">端口 1234</span>
                </button>
              </div>
            </Field>
            <Field label="服务地址">
              <input
                type="text"
                value={localUrl}
                onChange={e => setLocalUrl(e.target.value)}
                placeholder={localProvider === 'ollama' ? 'http://localhost:11434' : 'http://localhost:1234'}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </Field>
            <Field label="模型名称" hint="手动输入或留空后自动检测">
              <input
                type="text"
                value={localModel}
                onChange={e => setLocalModel(e.target.value)}
                placeholder="qwen2.5-coder:latest"
                className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </Field>
            <Field label={`温度参数: ${localTemp}`}>
              <input
                type="range" min="0" max="1" step="0.1"
                value={localTemp}
                onChange={e => setLocalTemp(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>精确 (0)</span><span>创意 (1)</span>
              </div>
            </Field>
            <LocalFirstToggle checked={localFirst} onChange={setLocalFirst} />
          </ConfigCard>
        )}

        {activeTab === 'status' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">连接状态</h2>
              <button type="button"
                onClick={fetchStatus}
                disabled={isRefreshing}
                className="text-sm text-primary hover:text-primary/80 flex items-center gap-1"
              >
                <ChevronRight className={cn('w-4 h-4', isRefreshing && 'animate-spin')} />
                刷新
              </button>
            </div>
            {isRefreshing && !status ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : status ? (
              <>
                <div className="p-4 bg-muted rounded-lg">
                  <div className="text-sm font-medium mb-2">当前激活</div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold">{status.current_provider}</span>
                    <span className="text-muted-foreground">/</span>
                    <span>{status.current_model}</span>
                    {status.is_local_first && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">本地优先</span>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {status.providers.map(p => (
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

// ========================================
// Sub-components
// ========================================

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-foreground">{label}</label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

/** 行业标准 API Key 输入组件：预览 + 替换/删除 */
function ApiKeyField({
  label,
  hasKey,
  preview,
  keyLength,
  value,
  onChange,
  replaceMode,
  onEnterReplace,
  onCancelReplace,
  onDelete,
  placeholder,
}: {
  label: string
  hasKey: boolean
  preview: string
  keyLength: number
  value: string
  onChange: (v: string) => void
  replaceMode: boolean
  onEnterReplace: () => void
  onCancelReplace: () => void
  onDelete: () => void
  placeholder?: string
}) {
  // 纯掩码预览：只显示前缀4位 + 对应数量的点 + 后缀4位
  const maskedPreview = hasKey && keyLength > 0
    ? `${'•'.repeat(keyLength)}`
    : ''

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        {hasKey && !replaceMode ? (
          <>
            {/* 预览框：显示全掩码 */}
            <div className="flex-1 px-3 py-2 border border-border rounded-lg text-sm bg-muted/50 text-muted-foreground font-mono tracking-widest overflow-hidden text-ellipsis whitespace-nowrap">
              {maskedPreview}
            </div>
            {/* 替换按钮 */}
            <button type="button"
              type="button"
              onClick={onEnterReplace}
              className="flex items-center gap-1 px-3 py-2 text-sm border border-primary text-primary rounded-lg hover:bg-primary/10 transition-colors shrink-0"
            >
              <Pencil className="w-3.5 h-3.5" />
              替换
            </button>
            {/* 删除按钮 */}
            <button type="button"
              type="button"
              onClick={onDelete}
              className="flex items-center gap-1 px-3 py-2 text-sm border border-red-300 text-red-500 rounded-lg hover:bg-red-50 transition-colors shrink-0"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </>
        ) : !replaceMode ? (
          /* 未配置时：输入框 */
          <input
            type="text"
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder || '输入 API 密钥'}
            className="flex-1 px-3 py-2 border border-border rounded-lg text-sm bg-background font-mono focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        ) : (
          /* 替换模式：输入框 + 取消 */
          <>
            <input
              type="text"
              value={value}
              onChange={e => onChange(e.target.value)}
              placeholder={placeholder || '输入新密钥'}
              autoFocus
              className="flex-1 px-3 py-2 border border-border rounded-lg text-sm bg-background font-mono focus:ring-2 focus:ring-primary focus:border-transparent"
            />
            <button type="button"
              type="button"
              onClick={onCancelReplace}
              className="px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors shrink-0"
            >
              取消
            </button>
          </>
        )}
      </div>

      {/* 替换模式下显示提示 */}
      {replaceMode && (
        <p className="text-xs text-muted-foreground">
          {value ? `将替换为新密钥（${value.length} 位）` : '输入为空将删除现有密钥'}
        </p>
      )}
    </div>
  )
}

function LocalFirstToggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
      <div>
        <div className="text-sm font-medium">本地优先模式</div>
        <div className="text-xs text-muted-foreground">优先使用本地模型，本地不可用时 fallback 到云端</div>
      </div>
      <button type="button"
        type="button"
        onClick={() => onChange(!checked)}
        className={cn(
          'relative w-11 h-6 rounded-full transition-colors',
          checked ? 'bg-primary' : 'bg-muted-foreground/30'
        )}
      >
        <span className={cn(
          'absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform',
          checked && 'translate-x-5'
        )} />
      </button>
    </div>
  )
}

function ConfigCard({
  title,
  description,
  icon,
  isSaving,
  isTesting,
  testResult,
  onSave,
  onTest,
  children,
}: {
  title: string
  description: string
  icon: React.ReactNode
  isSaving: boolean
  isTesting: boolean
  testResult: TestConnectionResponse | null
  onSave: () => void
  onTest: () => void
  children: React.ReactNode
}) {
  return (
    <div className="bg-card rounded-lg shadow p-6 space-y-5">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg text-primary">{icon}</div>
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="space-y-5">
        {children}

        {/* Test Connection row */}
        <div className="flex items-center gap-3 pt-2 border-t">
          <button type="button"
            onClick={onTest}
            disabled={isTesting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-primary text-primary rounded-lg hover:bg-primary/10 disabled:opacity-50 transition-colors"
          >
            {isTesting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            {isTesting ? '测试中...' : '测试连接'}
          </button>
          {testResult && (
            <div className={cn(
              'flex items-center gap-2 text-sm',
              testResult.success ? 'text-emerald-600' : 'text-red-500'
            )}>
              {testResult.success ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <AlertCircle className="w-4 h-4" />
              )}
              <span>{testResult.message}</span>
              {testResult.latency_ms !== undefined && (
                <span className="text-xs text-muted-foreground">({testResult.latency_ms}ms)</span>
              )}
            </div>
          )}
        </div>
      </div>
      <button type="button"
        onClick={onSave}
        disabled={isSaving}
        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        {isSaving ? '保存中...' : '保存配置'}
      </button>
    </div>
  )
}

function ProviderCard({ provider }: { provider: ProviderStatus }) {
  const isConnected = provider.status === 'connected'
  const Icon = isConnected ? Wifi : WifiOff
  const iconColor = isConnected ? 'text-emerald-600' : 'text-red-500'

  return (
    <div className="bg-card rounded-lg shadow p-4 border">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={cn('w-4 h-4', iconColor)} />
          <span className="font-medium capitalize">{provider.type === 'lmstudio' ? 'LM Studio' : provider.type}</span>
        </div>
        <span className={cn(
          'text-xs px-2 py-0.5 rounded-full',
          isConnected ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
        )}>
          {isConnected ? '已连接' : '未连接'}
        </span>
      </div>
      <div className="space-y-1 text-xs text-muted-foreground">
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
