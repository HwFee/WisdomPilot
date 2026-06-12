export const metadata = {
  title: '经验值 - 智码领航',
  description: '查看你的学习经验值（XP）与等级进度',
}

import { Zap } from "lucide-react"
import { EmptyState } from "@/components/layout"

export default function XpPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="max-w-[1280px] mx-auto">
        <EmptyState
          icon={Zap}
          title="经验流水"
          description="记录经验值（XP）的获取途径与累计。流水数据正在准备中。"
          primaryAction={{ label: "返回学习中心", href: "/dashboard" }}
        />
      </div>
    </main>
  )
}
