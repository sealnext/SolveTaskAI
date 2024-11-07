import * as React from "react"
import * as SwitchPrimitives from "@radix-ui/react-switch"
import { cn } from "@/lib/utils"
import { Moon, Sun } from "lucide-react"

const ThemeSwitch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitives.Root
    className={cn(
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
      "disabled:cursor-not-allowed disabled:opacity-50",
      props.checked ? "bg-primary" : "bg-muted",
      className
    )}
    {...props}
    ref={ref}
  >
    <SwitchPrimitives.Thumb className={cn(
      "pointer-events-none flex items-center justify-center h-5 w-5 rounded-full bg-white",
      "shadow-lg ring-0 transition-transform duration-200 ease-in-out",
      props.checked ? "translate-x-5" : "translate-x-0"
    )}>
      <div className={cn(
        "transition-opacity duration-200",
        props.checked ? "opacity-100" : "opacity-0"
      )}>
        <Moon className="h-3 w-3 text-primary" />
      </div>
      <div className={cn(
        "absolute transition-opacity duration-200",
        props.checked ? "opacity-0" : "opacity-100"
      )}>
        <Sun className="h-3 w-3 text-primary" />
      </div>
    </SwitchPrimitives.Thumb>
  </SwitchPrimitives.Root>
))
ThemeSwitch.displayName = "ThemeSwitch"

export { ThemeSwitch } 