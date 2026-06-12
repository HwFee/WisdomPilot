import type { Metadata } from "next"
import RegisterPageClient from "./page-client"

export const metadata: Metadata = {
  title: "注册 - 智码领航",
  description: "注册智码领航账户",
}

export default function RegisterPage() {
  return <RegisterPageClient />
}
