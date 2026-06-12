import type { Metadata } from 'next'
import ForgotPasswordClient from './page-client'

export const metadata: Metadata = {
  title: '找回密码 - 智码领航',
  description: '通过注册邮箱重置你的智码领航账号密码',
}

export default function Page() {
  return <ForgotPasswordClient />
}
