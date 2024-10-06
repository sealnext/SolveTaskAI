import * as React from "react"
import { cn } from "@/lib/utils"
import { Eye, EyeOff } from "lucide-react" // Importăm iconițele pentru vizualizarea parolei

const Input = React.forwardRef(({ className, type, icon: Icon, label, ...props }, ref) => {
  const [showPassword, setShowPassword] = React.useState(false)
  const isPassword = type === "password"

  return (
    <div className="w-full space-y-2">
      {label && (
        <label className="block text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted" size={18} />
        )}
        <input
          type={isPassword && showPassword ? "text" : type}
          className={cn(
            "flex h-12 w-full rounded-[10px] border border-muted bg-background px-3 py-2 text-sm shadow-sm transition-colors",
            "text-foreground",
            "file:border-0 file:bg-transparent file:text-sm file:font-medium",
            "placeholder:text-muted-foreground",
            "focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "autofill-fix",
            Icon ? "pl-10" : "pl-3",
            isPassword ? "pr-10" : "pr-3",
            className
          )}
          ref={ref}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted hover:text-foreground focus:outline-none"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
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
