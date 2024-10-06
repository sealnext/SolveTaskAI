'use client'

import { SessionProvider } from "next-auth/react"
import { ThemeProvider } from "@/contexts/ThemeContext"

export default function Provider({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </SessionProvider>
  )
}