'use client'

import { SessionProvider } from "next-auth/react"
import { ThemeProvider } from "@/contexts/ThemeContext"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

export default function Provider({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient()
  
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </SessionProvider>
    </QueryClientProvider>
  )
}