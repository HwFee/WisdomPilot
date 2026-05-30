"use client"

import { AIContextProvider } from "@/contexts/AIContext"
import { LazyMotion, domAnimation } from "framer-motion"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <LazyMotion features={domAnimation}>
      <AIContextProvider>
        {children}
      </AIContextProvider>
    </LazyMotion>
  )
}
