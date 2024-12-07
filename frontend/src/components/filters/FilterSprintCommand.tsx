import * as React from "react"
import { Timer, ChevronLeft, Plus, X } from "lucide-react"
import { CommandList } from "cmdk"
import { cn } from "@/lib/utils"
import { BaseFilterCommandProps } from "./types"

export function FilterSprintCommand({ 
  activeFilters, 
  onActiveFiltersChange,
  onBack 
}: BaseFilterCommandProps) {
  const [sprintName, setSprintName] = React.useState("")
  const [error, setError] = React.useState<string | null>(null)
  const inputRef = React.useRef<HTMLInputElement>(null)

  const sprintFilters = React.useMemo(() => {
    return activeFilters.filter(filter => filter.icon === Timer)
  }, [activeFilters])

  React.useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleAddSprint = () => {
    const trimmedName = sprintName.trim()
    if (!trimmedName) {
      setError("Sprint name cannot be empty")
      return
    }

    if (sprintFilters.some(f => f.id.toLowerCase() === trimmedName.toLowerCase())) {
      setError("This sprint is already added")
      return
    }

    const newFilter = {
      id: trimmedName,
      label: trimmedName,
      icon: Timer
    }

    onActiveFiltersChange([...activeFilters, newFilter])
    setSprintName("")
    setError(null)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleAddSprint()
    }
  }

  return (
    <>
      {/* Header */}
      <div className="flex-none w-full px-4 py-3 border-b border-muted/20">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-1.5 -ml-1.5 hover:bg-muted/10 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div className="flex-1">
            <h4 className="text-base font-medium leading-none mb-1">Sprint</h4>
            <p className="text-xs text-muted-foreground/70">Add sprint filters</p>
          </div>
        </div>
      </div>

      {/* Input Section */}
      <div className="flex-none w-full px-4 py-3 border-b border-muted/20 bg-muted/[0.015]">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            placeholder="Sprint name"
            value={sprintName}
            onChange={(e) => {
              setSprintName(e.target.value)
              setError(null)
            }}
            onKeyDown={handleKeyDown}
            className={cn(
              "flex-1 px-3 py-1.5 text-sm",
              "bg-background hover:bg-muted/5 focus:bg-background",
              "rounded-lg border shadow-sm",
              "outline-none ring-1 ring-transparent",
              "transition-all duration-150 ease-in-out",
              "h-9",
              error 
                ? "border-red-500/30 focus:border-red-500/30 focus:ring-red-500/10" 
                : "border-muted/20 focus:border-primary/20 focus:ring-primary/10"
            )}
          />
          <button
            onClick={handleAddSprint}
            disabled={!sprintName.trim()}
            className={cn(
              "flex items-center justify-center",
              "h-9 w-9 rounded-lg",
              "transition-all duration-150 ease-in-out",
              "border shadow-sm",
              sprintName.trim()
                ? "bg-primary border-primary/20 text-primary-foreground hover:bg-primary/90"
                : "bg-background border-muted/20 text-muted-foreground/50"
            )}
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        
        {error && (
          <p className="text-xs text-red-500/90 mt-2 flex items-center gap-1.5">
            <X className="h-3 w-3" />
            {error}
          </p>
        )}
      </div>

      {/* Active Filters */}
      <CommandList className="flex-1 min-h-0 overflow-auto">
        <div className="p-3">
          {sprintFilters.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-2">
              <div className="p-3 rounded-xl bg-muted/5 border border-muted/10">
                <Timer className="h-5 w-5 text-muted-foreground/40" />
              </div>
              <p className="text-sm text-muted-foreground/70">No sprint filters</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
              {sprintFilters.map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => onActiveFiltersChange(activeFilters.filter(f => f.id !== filter.id))}
                  className={cn(
                    "group relative w-full flex items-center gap-2.5",
                    "px-3 py-2 rounded-lg",
                    "bg-background hover:bg-muted/5",
                    "border border-muted/10",
                    "shadow-[0_2px_4px_rgba(0,0,0,0.02)] hover:shadow-[0_4px_8px_rgba(0,0,0,0.04)]",
                    "transition-all duration-200 ease-in-out"
                  )}
                >
                  {/* Sprint icon */}
                  <div className={cn(
                    "relative shrink-0 w-6 h-6 rounded-xl",
                    "flex items-center justify-center",
                    "bg-primary/5 group-hover:bg-primary/10",
                    "shadow-sm group-hover:shadow",
                    "transition-all duration-200"
                  )}>
                    <Timer className="h-3.5 w-3.5 text-primary/70" />
                  </div>

                  {/* Sprint name */}
                  <div className="flex-1 truncate text-sm">
                    {filter.label}
                  </div>

                  {/* Remove button */}
                  <div className={cn(
                    "shrink-0 w-6 h-6 rounded-xl",
                    "flex items-center justify-center",
                    "opacity-0 group-hover:opacity-100",
                    "transition-all duration-200",
                    "hover:bg-red-500/10 hover:shadow-sm",
                    "text-muted-foreground/40 hover:text-red-500"
                  )}>
                    <X className="h-3.5 w-3.5" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </CommandList>
    </>
  )
} 