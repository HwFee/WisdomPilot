import type { Metadata } from 'next'
import { ProfileClient } from '@/components/profile/ProfileClient'

export const metadata: Metadata = {
  title: '档案 · 智码领航',
}

export default function ProfilePage() {
  return <ProfileClient />
}
