import * as React from "react"
import { Search, Tag, ChevronLeft, Plus, AlertCircle, X } from "lucide-react"
import { CommandList } from "../ui/command"
import { cn } from "@/lib/utils"
import { Filter, BaseFilterCommandProps } from "./types"

interface Label {
  id: string;
  name: string;
  count?: number;
}

const PREDEFINED_GROUPS = {
  type: {
    icon: "📋",
    labels: ["bug", "feature", "improvement", "enhancement"]
  },
  priority: {
    icon: "🎯",
    labels: ["urgent", "high", "medium", "low"]
  },
  area: {
    icon: "🔧",
    labels: ["frontend", "backend", "api", "docs", "testing"]
  }
}

const POPULAR_LABELS = [
  { id: "bug", name: "bug"},
  { id: "feature", name: "feature"},
  { id: "urgent", name: "urgent" },
  { id: "backend", name: "backend",}
  // { id: "backend", name: "backend", count: 12 }
]

// Adăugăm culori predefinite pentru label groups
const GROUP_COLORS = {
  type: {
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    text: "text-blue-500",
    hover: "hover:bg-blue-500/20"
  },
  priority: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    text: "text-amber-500",
    hover: "hover:bg-amber-500/20"
  },
  area: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    text: "text-emerald-500",
    hover: "hover:bg-emerald-500/20"
  }
}

export function FilterLabelsCommand({ 
  projectId, 
  activeFilters, 
  onActiveFiltersChange,
  onBack 
}: BaseFilterCommandProps) {
  const [searchTerm, setSearchTerm] = React.useState("")
  const [labels, setLabels] = React.useState<Label[]>(POPULAR_LABELS)
  const [isCreatingNew, setIsCreatingNew] = React.useState(false)

  // Normalize label text
  const normalizeLabel = (text: string) => {
    return text.toLowerCase().trim().replace(/[^a-z0-9-]/g, '-')
  }

  // Check if a label is similar to existing ones
  const findSimilarLabels = (text: string): Label[] => {
    const normalized = normalizeLabel(text)
    return labels.filter(label => 
      label.name.includes(normalized) || 
      normalized.includes(label.name)
    )
  }

  const handleCreateLabel = () => {
    if (!searchTerm.trim()) return

    const normalized = normalizeLabel(searchTerm)
    const newLabel = {
      id: normalized,
      name: normalized,
      count: 0
    }

    setLabels(prev => [...prev, newLabel])
    const newFilter = {
      id: newLabel.id,
      label: `"${newLabel.name}"`,
      icon: Tag
    }
    onActiveFiltersChange([...activeFilters, newFilter])
    setSearchTerm("")
    setIsCreatingNew(false)
  }

  const handleLabelClick = (label: Label) => {
    const isSelected = activeFilters.some(f => f.id === label.id)
    
    if (isSelected) {
      onActiveFiltersChange(activeFilters.filter(f => f.id !== label.id))
    } else {
      const newFilter = {
        id: label.id,
        label: `"${label.name}"`,
        icon: Tag
      }
      onActiveFiltersChange([...activeFilters, newFilter])
    }
  }

  // Filter and sort labels based on search
  const filteredLabels = React.useMemo(() => {
    if (!searchTerm) return labels
    
    const normalized = normalizeLabel(searchTerm)
    return labels
      .filter(label => label.name.includes(normalized))
      .sort((a, b) => {
        // Exact matches first
        if (a.name === normalized) return -1
        if (b.name === normalized) return 1
        // Then by usage count
        return (b.count || 0) - (a.count || 0)
      })
  }, [labels, searchTerm])

  // Check if we should show create option
  const shouldShowCreate = searchTerm.trim() && 
    !labels.some(l => l.name === normalizeLabel(searchTerm))

  // Get custom labels (labels that are in activeFilters but not in predefined groups)
  const customLabels = React.useMemo(() => {
    const predefinedLabels = new Set([
      ...POPULAR_LABELS.map(l => l.id),
      ...Object.values(PREDEFINED_GROUPS).flatMap(group => group.labels)
    ])
    
    return activeFilters.filter(filter => !predefinedLabels.has(filter.id))
  }, [activeFilters])

  return (
    <>
      {/* Header with search and back */}
      <div className="w-full p-2 border-b border-muted/30 bg-gradient-to-b from-muted/10 to-transparent">
        <div className="flex items-center gap-3 px-2">
          <button
            onClick={onBack}
            className="p-1.5 hover:bg-muted/20 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div>
            <h4 className="text-sm font-medium">Labels</h4>
            <p className="text-xs text-muted-foreground">Add or create labels</p>
          </div>
        </div>
      </div>

      {/* Filter Content */}
      <CommandList className="w-full">
        <div className="p-4">
          {/* Search input - Sticky */}
          <div className="sticky top-0 z-10 pb-4 backdrop-blur-sm">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50" />
              <input
                type="text"
                placeholder="Search or create label..."
                className={cn(
                  "w-full pl-9 pr-4 py-1.5 text-sm",
                  "bg-muted/5 hover:bg-muted/10 focus:bg-muted/10",
                  "rounded-lg border border-muted/20 focus:border-primary/30",
                  "outline-none ring-2 ring-transparent focus:ring-primary/10",
                  "transition-all duration-150 ease-in-out",
                  "h-[32px]"
                )}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {/* Content Container */}
          <div className="space-y-6">
            {searchTerm ? (
              <>
                {/* Matching Labels */}
                {filteredLabels.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="text-xs font-medium text-muted-foreground">Matching Labels</div>
                      <div className="h-px flex-1 bg-muted/20"></div>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {filteredLabels.map(label => {
                        const isSelected = activeFilters.some(f => f.id === label.id)
                        return (
                          <button
                            key={label.id}
                            onClick={() => handleLabelClick(label)}
                            className={cn(
                              "group relative flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm",
                              "hover:bg-muted/10",
                              "border border-transparent",
                              isSelected && "bg-primary/5 border-primary/20"
                            )}
                          >
                            <Tag className={cn(
                              "h-3.5 w-3.5",
                              isSelected ? "text-primary" : "text-muted-foreground/70"
                            )} />
                            <span className={cn(
                              isSelected && "text-primary"
                            )}>
                              {label.name}
                            </span>
                            {label.count && (
                              <span className={cn(
                                "text-xs px-1.5 py-0.5 rounded-md ml-auto",
                                isSelected ? "bg-primary/20 text-primary" : "bg-muted/20 text-muted-foreground"
                              )}>
                                {label.count}
                              </span>
                            )}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Create New Option */}
                {shouldShowCreate && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="text-xs font-medium text-muted-foreground">Create New</div>
                      <div className="h-px flex-1 bg-muted/20"></div>
                    </div>
                    <button
                      onClick={handleCreateLabel}
                      className={cn(
                        "w-full flex items-center gap-3 p-3 rounded-lg",
                        "bg-primary/5 hover:bg-primary/10",
                        "border border-primary/20",
                        "transition-all duration-150"
                      )}
                    >
                      <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                        <Plus className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 text-left">
                        <div className="text-sm font-medium text-primary">Create new label</div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          &quot;{normalizeLabel(searchTerm)}&quot;
                        </div>
                      </div>
                      {findSimilarLabels(searchTerm).length > 0 && (
                        <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-yellow-500/10 border border-yellow-500/20">
                          <AlertCircle className="h-3.5 w-3.5 text-yellow-500" />
                          <span className="text-xs text-yellow-500">Similar exists</span>
                        </div>
                      )}
                    </button>
                  </div>
                )}

                {/* No Results */}
                {filteredLabels.length === 0 && !shouldShowCreate && (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <AlertCircle className="h-8 w-8 text-muted-foreground/50 mb-2" />
                    <p className="text-sm text-muted-foreground">No matching labels found</p>
                  </div>
                )}
              </>
            ) : (
              <>
                {/* Active Custom Labels Section */}
                {customLabels.length > 0 && (
                  <div className="space-y-3 mb-6">
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-2 text-xs font-medium text-primary-accent">
                        <div className="h-1.5 w-1.5 rounded-full animate-pulse bg-primary-accent"></div>
                        Active Custom Labels
                      </div>
                      <div className="h-px flex-1 bg-muted/20"></div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {customLabels.map(label => (
                        <button
                          key={label.id}
                          onClick={() => onActiveFiltersChange(activeFilters.filter(f => f.id !== label.id))}
                          className={cn(
                            "group relative flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm",
                            "bg-primary-accent/5 hover:bg-primary-accent/10",
                            "border border-primary-accent/20",
                            "transition-all duration-200 ease-out"
                          )}
                        >
                          <Tag className="h-3.5 w-3.5 text-primary-accent" />
                          <span className="text-sm text-primary-accent">
                            {label.label.replace(/"/g, '')}
                          </span>
                          <X 
                            className={cn(
                              "h-3.5 w-3.5 ml-1.5",
                              "text-primary-accent/40 hover:text-primary-accent",
                              "opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                            )} 
                          />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quick Add Section */}
                <div className="space-y-3 mb-6">
                  <div className="flex items-center gap-2">
                    <div className="text-xs font-medium text-muted-foreground">Quick Add</div>
                    <div className="h-px flex-1 bg-muted/20"></div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {POPULAR_LABELS.map(label => {
                      const isSelected = activeFilters.some(f => f.id === label.id)
                      return (
                        <button
                          key={label.id}
                          onClick={() => handleLabelClick(label)}
                          className={cn(
                            "group relative flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm",
                            "hover:bg-muted/10",
                            "border border-transparent",
                            isSelected && "bg-primary/5 border-primary/20"
                          )}
                        >
                          <Tag className={cn(
                            "h-3.5 w-3.5",
                            isSelected ? "text-primary" : "text-muted-foreground/70"
                          )} />
                          <span className={cn(
                            isSelected && "text-primary"
                          )}>
                            {label.name}
                          </span>
                          {label.count && (
                            <span className={cn(
                              "text-xs px-1.5 py-0.5 rounded-md",
                              isSelected ? "bg-primary/20 text-primary" : "bg-muted/20 text-muted-foreground"
                            )}>
                              {label.count}
                            </span>
                          )}
                        </button>
                      )
                    })}
                  </div>
                </div>

                {/* Predefined Groups */}
                <div className="space-y-6">
                  {Object.entries(PREDEFINED_GROUPS).map(([groupName, group]) => {
                    const colors = GROUP_COLORS[groupName as keyof typeof GROUP_COLORS]
                    return (
                      <div key={groupName} className="space-y-3">
                        <div className="flex items-center gap-2">
                          <div className={cn(
                            "text-xs font-medium flex items-center gap-1.5",
                            colors.text
                          )}>
                            {group.icon} {groupName.charAt(0).toUpperCase() + groupName.slice(1)}
                          </div>
                          <div className="h-px flex-1 bg-muted/20"></div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {group.labels.map(labelName => {
                            const label = labels.find(l => l.name === labelName) || 
                              { id: labelName, name: labelName }
                            const isSelected = activeFilters.some(f => f.id === label.id)
                            
                            return (
                              <button
                                key={label.id}
                                onClick={() => handleLabelClick(label)}
                                className={cn(
                                  "group relative flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm",
                                  "hover:bg-muted/10",
                                  "border border-transparent",
                                  isSelected && colors.bg + " " + colors.border
                                )}
                              >
                                <Tag className={cn(
                                  "h-3.5 w-3.5",
                                  isSelected ? colors.text : "text-muted-foreground/70"
                                )} />
                                <span className={cn(
                                  isSelected && colors.text
                                )}>
                                  {label.name}
                                </span>
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            )}
          </div>
        </div>
      </CommandList>
    </>
  )
} 