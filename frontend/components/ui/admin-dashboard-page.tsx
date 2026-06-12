'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Shield, Users, UserCheck, Trash2, RefreshCw, LogOut } from 'lucide-react'

interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

function ClientDate({ dateStr }: { dateStr: string }) {
  const formatted = new Date(dateStr).toLocaleDateString('zh-CN')
  return <span suppressHydrationWarning>{formatted}</span>
}

function getAuthToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token:v1')
}

function getCurrentUser() {
  if (typeof window === 'undefined') return null
  try {
    return JSON.parse(localStorage.getItem('user:v1') || 'null')
  } catch {
    return null
  }
}

export default function AdminDashboardPage() {
  const { push } = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [onlineUsers, setOnlineUsers] = useState<User[]>([])
  const [status, setStatus] = useState({ isLoading: true, error: '' })
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const currentUser = getCurrentUser()

  const fetchUsers = useCallback(async () => {
    const token = getAuthToken()
    if (!token) return
    try {
      setStatus(prev => ({ ...prev, isLoading: true }))
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to fetch users')
      const data = await res.json()
      setUsers(data)
    } catch (err) {
      setStatus(prev => ({ ...prev, error: err instanceof Error ? err.message : 'Error fetching users' }))
    } finally {
      setStatus(prev => ({ ...prev, isLoading: false }))
    }
  }, [])

  useEffect(() => {
    const token = getAuthToken()
    const currentUser = getCurrentUser()
    if (!token || !currentUser?.is_admin) {
      push('/login')
      return
    }
    fetchUsers()
  }, [push, fetchUsers])

  const fetchOnlineUsers = async () => {
    const token = getAuthToken()
    if (!token) return
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/users/online`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to fetch online users')
      const data = await res.json()
      setOnlineUsers(data)
    } catch (err) {
      setStatus(prev => ({ ...prev, error: err instanceof Error ? err.message : 'Error fetching online users' }))
    }
  }

  const deleteUser = async (userId: string) => {
    const token = getAuthToken()
    if (!token) return
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to delete user')
      setUsers(prev => prev.filter(u => u.id !== userId))
      setDeleteConfirm(null)
    } catch (err) {
      setStatus(prev => ({ ...prev, error: err instanceof Error ? err.message : 'Error deleting user' }))
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token:v1')
    localStorage.removeItem('user:v1')
    push('/login')
  }

  if (status.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <RefreshCw className="size-8 animate-spin text-blue-600 mx-auto" />
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="size-8 text-blue-600" />
            <h1 className="text-2xl font-semibold text-gray-900">管理后台</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">管理员: {currentUser?.username}</span>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="size-4 mr-2" />
              退出登录
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {status.error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {status.error}
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-full">
                <Users className="size-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">总用户数</p>
                <p className="text-2xl font-bold text-gray-900">{users.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-full">
                <UserCheck className="size-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">在线用户</p>
                <p className="text-2xl font-bold text-gray-900">
                  <button type="button"
                    onClick={fetchOnlineUsers}
                    className="hover:text-green-600 underline"
                  >
                    {onlineUsers.length}
                  </button>
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-100 rounded-full">
                <UserCheck className="size-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">活跃用户</p>
                <p className="text-2xl font-bold text-gray-900">
                  {users.filter(u => u.is_active).length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">用户列表</h2>
            <Button variant="outline" size="sm" onClick={fetchUsers}>
              <RefreshCw className="size-4 mr-2" />
              刷新
            </Button>
          </div>

          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  用户名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  邮箱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  注册时间
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{user.username}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{user.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      user.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? '活跃' : '禁用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <ClientDate dateStr={user.created_at} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {deleteConfirm === user.id ? (
                      <div className="flex items-center justify-end gap-2">
                        <span className="text-red-600 text-xs">确认删除?</span>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => deleteUser(user.id)}
                        >
                          确认
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setDeleteConfirm(null)}
                        >
                          取消
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteConfirm(user.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {users.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              暂无用户
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
