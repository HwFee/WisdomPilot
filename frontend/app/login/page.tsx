import type { Metadata } from "next"
import LoginPageClient from "./page-client"

export const metadata: Metadata = {
  title: "登录 - 智码领航",
  description: "登录智码领航账户",
}

export default function LoginPage() {
  return <LoginPageClient />
}
