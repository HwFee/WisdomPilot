export const metadata = {
  title: '智核 - 智码领航',
  description: '查看和管理你的智核（ZhiHe）交易记录与余额',
}

import { Gem } from "lucide-react"
import { EmptyState } from "@/components/layout"

export default function CoresPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="max-w-[1280px] mx-auto">
        <EmptyState
          icon={Gem}
          title="智核流水"
          description="记录智核（Cores）的获取与消耗明细。流水数据正在准备中，敬请期待。"
          primaryAction={{ label: "返回学习中心", href: "/dashboard" }}
        />
      </div>
    </main>
  )
}
