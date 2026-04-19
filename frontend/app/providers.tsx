"use client"

import { AIContextProvider } from "@/contexts/AIContext"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AIContextProvider>
      {children}
    </AIContextProvider>
  )
}
