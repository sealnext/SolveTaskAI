import * as React from "react"
import { Command as CommandPrimitive } from "cmdk"
import { cn } from "@/lib/utils"

interface CommandDialogProps {
  children: React.ReactNode
  className?: string
  contentClassName?: string
}

export function CommandDialog({ 
  children,
  className,
  contentClassName
}: CommandDialogProps) {
  return (
    <div className={cn(
      "absolute bottom-full left-0 right-0 mb-4 w-full",
      className
    )}>
      <CommandPrimitive 
        className={cn(
          "w-full rounded-2xl border-2 border-muted",
          "overflow-hidden bg-backgroundSecondary bg-opacity-80",
          "backdrop-filter backdrop-blur-md shadow-lg",
          "h-[300px] flex flex-col",
          contentClassName
        )}
      >
        {children}
      </CommandPrimitive>
    </div>
  )
} 