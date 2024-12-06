import * as React from "react"
import { Search, Flag, ChevronLeft } from "lucide-react"
import { CommandList } from "cmdk"
import { cn } from "@/lib/utils"
import { BaseFilterCommandProps } from "./types"
import ApiClient from "@/lib/apiClient"
import Image from "next/image"

interface Priority {
  id: string;
  name: string;
  statusColor: string;
  description: string;
  iconUrl: string;
}

export function FilterPriorityCommand({ 
  projectId, 
  activeFilters, 
  onActiveFiltersChange,
  onBack 
}: BaseFilterCommandProps) {
  const [searchTerm, setSearchTerm] = React.useState("")
  const [isLoadingPriorities, setIsLoadingPriorities] = React.useState(true)
  const [priorities, setPriorities] = React.useState<Priority[]>([])
  const apiclient = React.useMemo(() => ApiClient(), [])

  React.useEffect(() => {
    const fetchPriorities = async () => {
      try {
        setIsLoadingPriorities(true);
        // TODO: to be implemented in backend
        // const data = await apiclient.getIssuePriorities(projectId.toString())
        const data = [
            {
              "self": "https://sealnext.atlassian.net/rest/api/2/priority/1",
              "statusColor": "#d04437",
              "description": "This problem will block progress.",
              "iconUrl": "https://sealnext.atlassian.net/images/icons/priorities/highest.svg",
              "name": "Highest",
              "id": "1"
            },
            {
              "self": "https://sealnext.atlassian.net/rest/api/2/priority/2",
              "statusColor": "#f15C75",
              "description": "Serious problem that could block progress.",
              "iconUrl": "https://sealnext.atlassian.net/images/icons/priorities/high.svg",
              "name": "High",
              "id": "2"
            },
            {
              "self": "https://sealnext.atlassian.net/rest/api/2/priority/3",
              "statusColor": "#f79232",
              "description": "Has the potential to affect progress.",
              "iconUrl": "https://sealnext.atlassian.net/images/icons/priorities/medium.svg",
              "name": "Medium",
              "id": "3"
            },
            {
              "self": "https://sealnext.atlassian.net/rest/api/2/priority/4",
              "statusColor": "#707070",
              "description": "Minor problem or easily worked around.",
              "iconUrl": "https://sealnext.atlassian.net/images/icons/priorities/low.svg",
              "name": "Low",
              "id": "4"
            },
            {
              "self": "https://sealnext.atlassian.net/rest/api/2/priority/5",
              "statusColor": "#999999",
              "description": "Trivial problem with little or no impact on progress.",
              "iconUrl": "https://sealnext.atlassian.net/images/icons/priorities/lowest.svg",
              "name": "Lowest",
              "id": "5"
            }
          ]
        // Transform the data to match our Priority interface
        const transformedPriorities = data.map((priority: any) => ({
          id: priority.id,
          name: priority.name,
          statusColor: priority.statusColor,
          description: priority.description,
          iconUrl: priority.iconUrl
        }))
        setPriorities(transformedPriorities)
      } catch (error) {
        console.error('Error fetching priorities:', error)
      } finally {
        setIsLoadingPriorities(false)
      }
    }

    fetchPriorities()
  }, [projectId, apiclient])

  // Filter priorities based on search term
  const filteredPriorities = React.useMemo(() => {
    if (!searchTerm) return priorities
    const normalized = searchTerm.toLowerCase()
    return priorities.filter(priority => 
      priority.name.toLowerCase().includes(normalized) ||
      priority.description.toLowerCase().includes(normalized)
    )
  }, [priorities, searchTerm])

  return (
    <>
      {/* Header with search and back */}
      <div className="flex-none w-full p-2 border-b border-muted/30 bg-gradient-to-b from-muted/10 to-transparent">
        <div className="flex items-center gap-3 px-2">
          <button
            onClick={onBack}
            className="p-1.5 hover:bg-muted/20 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div>
            <h4 className="text-sm font-medium">Priority</h4>
            <p className="text-xs text-muted-foreground">Set issue priority level</p>
          </div>
        </div>
      </div>

      {/* Search input - Sticky */}
      <div className="flex-none w-full p-4 pb-2 bg-background/80 backdrop-blur-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50" />
          <input
            type="text"
            placeholder="Search priorities..."
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

      {/* Filter Content - Scrollable */}
      <CommandList className="flex-1 min-h-0 overflow-auto">
        <div className="p-4 pt-2">
          {/* Content Container */}
          <div className="space-y-1.5">
            {isLoadingPriorities ? (
              // Loading state
              <div className="flex flex-col items-center justify-center py-8 space-y-4">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
                <p className="text-sm text-muted-foreground">Loading priorities...</p>
              </div>
            ) : filteredPriorities.length === 0 ? (
              // Empty state
              <div className="flex flex-col items-center justify-center py-8 space-y-2">
                <Flag className="h-8 w-8 text-muted-foreground/50" />
                <p className="text-sm text-muted-foreground">No priorities found</p>
              </div>
            ) : (
              // Priority grid with responsive columns
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {filteredPriorities.map((priority) => {
                  const isSelected = activeFilters.some(f => f.id === priority.id)
                  return (
                    <button
                      key={priority.id}
                      onClick={() => {
                        if (isSelected) {
                          onActiveFiltersChange(activeFilters.filter(f => f.id !== priority.id))
                        } else {
                          const newFilter = {
                            id: priority.id,
                            label: priority.name,
                            icon: Flag
                          }
                          onActiveFiltersChange([...activeFilters, newFilter])
                        }
                      }}
                      className={cn(
                        "group relative w-full flex items-center gap-3 px-3 py-2 rounded-lg",
                        "hover:bg-muted/10",
                        "border border-transparent",
                        isSelected && "bg-primary/5 border-primary/20"
                      )}
                    >
                      {/* Priority icon */}
                      <div 
                        className={cn(
                          "relative w-5 h-5 rounded-full",
                          "flex items-center justify-center",
                          "bg-gradient-to-b from-white/10 to-white/5",
                          "ring-1 ring-white/20"
                        )}
                        style={{ backgroundColor: priority.statusColor }}
                      >
                        <Image 
                          src={priority.iconUrl} 
                          alt={priority.name}
                          width={12}
                          height={12}
                          className="opacity-90"
                        />
                      </div>

                      {/* Priority details */}
                      <div className="flex-1 min-w-0">
                        <div className={cn(
                          "text-sm font-medium truncate",
                          isSelected && "text-primary"
                        )}>
                          {priority.name}
                        </div>
                        <div className="text-xs text-muted-foreground truncate">
                          {priority.description}
                        </div>
                      </div>

                      {/* Selected indicator */}
                      {isSelected && (
                        <div 
                          className="h-1.5 w-1.5 rounded-full bg-primary"
                          style={{ backgroundColor: priority.statusColor }}
                        />
                      )}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </CommandList>
    </>
  )
} 