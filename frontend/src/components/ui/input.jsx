import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, icon: Icon, ...props }, ref) => {
  return (
    <div className="relative">
      {Icon && (
        <Icon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted" size={18} />
      )}
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-[10px] border border-muted dark:bg-[var(--color-background)] px-3 py-1 text-sm shadow-sm transition-colors",
          "text-foreground",
          "file:border-0 file:bg-transparent file:text-sm file:font-medium",
          "placeholder:text-gray",
          "focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "autofill-fix", // Adăugat pentru autofill
          Icon ? "pl-10" : "pl-3",
          className
        )}
        ref={ref}
        {...props}
      />
      <style jsx global>{`
        .autofill-fix:-webkit-autofill,
        .autofill-fix:-webkit-autofill:hover,
        .autofill-fix:-webkit-autofill:focus {
          -webkit-text-fill-color: var(--color-foreground);
          -webkit-box-shadow: 0 0 0px 1000px var(--color-background) inset;
          transition: background-color 5000s ease-in-out 0s;
        }
      `}</style>
    </div>
  )
})
Input.displayName = "Input"

export { Input }
