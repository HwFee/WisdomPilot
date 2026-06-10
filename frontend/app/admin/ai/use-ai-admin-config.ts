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
  type TestConnectionResponse,
} from '@/lib/ai-api'

type TabId = 'deepseek' | 'minimax' | 'status'
type Message = { type: 'success' | 'error'; text: string } | null

export function useAIAdminConfig() {
  const { push } = useRouter()

  const [activeTab, setActiveTab] = useState<TabId>('deepseek')
  const [config, setConfig] = useState<AIConfigResponse | null>(null)
  const [status, setStatus] = useState<AIStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestConnectionResponse | null>(null)
  const [message, setMessage] = useState<Message>(null)

  // DeepSeek state
  const [deepseekKey, setDeepseekKey] = useState('')
  const [deepseekModel, setDeepseekModel] = useState('deepseek-v4-flash')
  const [deepseekTemp, setDeepseekTemp] = useState(0.7)
  const [deepseekUrl, setDeepseekUrl] = useState('')
  const [hasDeepseekKey, setHasDeepseekKey] = useState(false)
  const [deepseekKeyPreview, setDeepseekKeyPreview] = useState('')
  const [deepseekKeyLength, setDeepseekKeyLength] = useState(0)
  const [deepseekKeyReplaceMode, setDeepseekKeyReplaceMode] = useState(false)

  // MiniMax state
  const [minimaxKey, setMinimaxKey] = useState('')
  const [minimaxModel, setMinimaxModel] = useState('MiniMax-M2.7')
  const [minimaxTemp, setMinimaxTemp] = useState(0.7)
  const [minimaxUrl, setMinimaxUrl] = useState('https://api.minimaxi.com/anthropic')
  const [hasMinimaxKey, setHasMinimaxKey] = useState(false)
  const [minimaxKeyPreview, setMinimaxKeyPreview] = useState('')
  const [minimaxKeyLength, setMinimaxKeyLength] = useState(0)
  const [minimaxKeyReplaceMode, setMinimaxKeyReplaceMode] = useState(false)

  const [localFirst, setLocalFirst] = useState(false)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token:v1') : null
  const currentUser = typeof window !== 'undefined'
    ? JSON.parse(localStorage.getItem('user:v1') || 'null')
    : null

  const showMessage = useCallback((type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 4000)
  }, [])

  const applyConfig = useCallback((data: AIConfigResponse) => {
    setLocalFirst(data.is_local_first)
    setHasDeepseekKey(data.provider === 'deepseek' && data.has_api_key)
    setHasMinimaxKey(data.provider === 'minimax' && data.has_api_key)
    setMinimaxKeyPreview(data.api_key_preview || '')
    setMinimaxKeyLength(data.api_key_length || 0)
    setMinimaxKeyReplaceMode(false)
    setMinimaxKey('')
    if (data.provider === 'deepseek') {
      setDeepseekKeyPreview(data.has_api_key ? (data.api_key_preview || '****') : '')
      setDeepseekKeyLength(data.api_key_length || 0)
    }
    setDeepseekKeyReplaceMode(false)
    setDeepseekKey('')
    if (data.provider === 'deepseek') {
      setActiveTab('deepseek')
    } else if (data.provider === 'minimax') {
      setActiveTab('minimax')
    }
  }, [])

  const fetchConfig = useCallback(async () => {
    if (!token) return
    try {
      setIsLoading(true)
      const data = await getAIConfig(token)
      setConfig(data)
      applyConfig(data)
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : '获取配置失败' })
    } finally {
      setIsLoading(false)
    }
  }, [token, applyConfig])

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
    if (!token || !currentUser?.is_admin) {
      push('/login')
      return
    }
    fetchConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (activeTab === 'status') {
      fetchStatus()
    }
  }, [activeTab, fetchStatus])

  const handleSaveDeepSeek = useCallback(async () => {
    if (!token) return
    setIsSaving(true)
    try {
      const updateRequest: UpdateAIConfigRequest = {
        provider: 'deepseek',
        temperature: deepseekTemp,
        model: deepseekModel,
      }
      if (deepseekKeyReplaceMode) {
        updateRequest.api_key = deepseekKey || ''
      } else if (deepseekKey) {
        updateRequest.api_key = deepseekKey
      }
      if (deepseekUrl.trim()) updateRequest.base_url = deepseekUrl.trim()
      updateRequest.is_local_first = localFirst
      await updateAIConfig(token, updateRequest)
      setDeepseekKey('')
      setDeepseekKeyReplaceMode(false)
      showMessage('success', 'DeepSeek 配置已保存')
      fetchConfig()
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : '保存失败')
    } finally {
      setIsSaving(false)
    }
  }, [token, deepseekTemp, deepseekModel, deepseekKey, deepseekKeyReplaceMode, deepseekUrl, localFirst, showMessage, fetchConfig])

  const handleSaveMinimax = useCallback(async () => {
    if (!token) return
    setIsSaving(true)
    try {
      const updateRequest: UpdateAIConfigRequest = {
        provider: 'minimax',
        temperature: minimaxTemp,
        model: minimaxModel,
      }
      if (minimaxKeyReplaceMode) {
        updateRequest.api_key = minimaxKey || ''
      } else if (minimaxKey) {
        updateRequest.api_key = minimaxKey
      }
      if (minimaxUrl.trim()) updateRequest.base_url = minimaxUrl.trim()
      updateRequest.is_local_first = localFirst
      await updateAIConfig(token, updateRequest)
      setMinimaxKey('')
      setMinimaxKeyReplaceMode(false)
      showMessage('success', 'MiniMax 配置已保存')
      fetchConfig()
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : '保存失败')
    } finally {
      setIsSaving(false)
    }
  }, [token, minimaxTemp, minimaxModel, minimaxKey, minimaxKeyReplaceMode, minimaxUrl, localFirst, showMessage, fetchConfig])

  const handleTestDeepSeek = useCallback(async () => {
    if (!token) return
    setIsTesting(true)
    setTestResult(null)
    try {
      const result = await testAIConnection(token, {
        provider: 'deepseek',
        api_key: deepseekKey || undefined,
        model: deepseekModel,
        base_url: deepseekUrl || undefined,
      })
      setTestResult(result)
    } catch (err) {
      setTestResult({ success: false, message: err instanceof Error ? err.message : '测试失败' })
    } finally {
      setIsTesting(false)
    }
  }, [token, deepseekKey, deepseekModel, deepseekUrl])

  const handleTestMinimax = useCallback(async () => {
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
  }, [token, minimaxKey, minimaxModel, minimaxUrl])

  const handleDeleteDeepseekKey = useCallback(async () => {
    if (!token) return
    setIsSaving(true)
    try {
      await updateAIConfig(token, { provider: 'deepseek', api_key: '' })
      setDeepseekKeyPreview('')
      setDeepseekKeyLength(0)
      showMessage('success', '密钥已删除')
      fetchConfig()
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : '删除失败')
    } finally {
      setIsSaving(false)
    }
  }, [token, showMessage, fetchConfig])

  const handleDeleteMinimaxKey = useCallback(async () => {
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
  }, [token, showMessage, fetchConfig])

  return {
    push,
    activeTab,
    setActiveTab,
    config,
    status,
    isLoading,
    isSaving,
    isRefreshing,
    isTesting,
    testResult,
    message,
    // DeepSeek
    deepseekKey,
    setDeepseekKey,
    deepseekModel,
    setDeepseekModel,
    deepseekTemp,
    setDeepseekTemp,
    deepseekUrl,
    setDeepseekUrl,
    hasDeepseekKey,
    deepseekKeyPreview,
    deepseekKeyLength,
    deepseekKeyReplaceMode,
    setDeepseekKeyReplaceMode,
    // MiniMax
    minimaxKey,
    setMinimaxKey,
    minimaxModel,
    setMinimaxModel,
    minimaxTemp,
    setMinimaxTemp,
    minimaxUrl,
    setMinimaxUrl,
    hasMinimaxKey,
    minimaxKeyPreview,
    minimaxKeyLength,
    minimaxKeyReplaceMode,
    setMinimaxKeyReplaceMode,
    // Common
    localFirst,
    setLocalFirst,
    token,
    // Actions
    fetchConfig,
    fetchStatus,
    showMessage,
    handleSaveDeepSeek,
    handleSaveMinimax,
    handleTestDeepSeek,
    handleTestMinimax,
    handleDeleteDeepseekKey,
    handleDeleteMinimaxKey,
  }
}
