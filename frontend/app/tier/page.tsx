export const metadata = {
  title: '段位 - 智码领航',
  description: '查看你的学习段位、晋级记录与特权',
}

import { Trophy } from "lucide-react"
import { EmptyState } from "@/components/layout"

export default function TierPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="max-w-[1280px] mx-auto">
        <EmptyState
          icon={Trophy}
          title="段位流水"
          description="记录段位（Tier）的升降与积分变化。流水数据正在准备中。"
          primaryAction={{ label: "返回学习中心", href: "/dashboard" }}
        />
      </div>
    </main>
  )
}
