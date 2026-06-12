'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Panel, PanelHeader } from '@/components/layout/Panel'
import { StatsGrid, StatCell } from '@/components/layout/StatsGrid'
import { Shield, Users, UserCheck, RefreshCw, LogOut } from 'lucide-react'

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
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <RefreshCw className="size-8 animate-spin text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="max-w-7xl mx-auto p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="size-8 text-primary" />
            <h1 className="text-2xl font-semibold text-foreground">管理后台</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-muted-foreground">管理员: {currentUser?.username}</span>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="size-4 mr-2" />
              退出登录
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {status.error && (
          <div className="mb-4 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive">
            {status.error}
          </div>
        )}

        {/* Stats Cards */}
        <StatsGrid className="mb-8">
          <StatCell>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded-full">
                <Users className="size-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">总用户数</p>
                <p className="text-2xl font-bold text-foreground">{users.length}</p>
              </div>
            </div>
          </StatCell>

          <StatCell>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-success/10 rounded-full">
                <UserCheck className="size-6 text-success" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">在线用户</p>
                <p className="text-2xl font-bold text-foreground">
                  <button
                    type="button"
                    onClick={fetchOnlineUsers}
                    className="hover:text-success underline"
                  >
                    {onlineUsers.length}
                  </button>
                </p>
              </div>
            </div>
          </StatCell>

          <StatCell>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-warning/10 rounded-full">
                <UserCheck className="size-6 text-warning" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">活跃用户</p>
                <p className="text-2xl font-bold text-foreground">
                  {users.filter(u => u.is_active).length}
                </p>
              </div>
            </div>
          </StatCell>
        </StatsGrid>

        {/* Users Table */}
        <Panel>
          <PanelHeader
            title="用户列表"
            action={
              <Button variant="outline" size="sm" onClick={fetchUsers}>
                <RefreshCw className="size-4 mr-2" />
                刷新
              </Button>
            }
          />

          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted">
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  用户名
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  邮箱
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  注册时间
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-foreground">{user.username}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        user.is_active
                          ? 'bg-success/10 text-success'
                          : 'bg-destructive/10 text-destructive'
                      }`}
                    >
                      {user.is_active ? '活跃' : '禁用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                    <ClientDate dateStr={user.created_at} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {deleteConfirm === user.id ? (
                      <div className="flex items-center justify-end gap-2">
                        <span className="text-destructive text-xs">确认删除?</span>
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
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        aria-label={`删除用户 ${user.username}`}
                      >
                        删除
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {users.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              暂无用户
            </div>
          )}
        </Panel>
      </main>
    </div>
  )
}
