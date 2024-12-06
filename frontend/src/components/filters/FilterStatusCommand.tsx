import * as React from "react"
import { Search, AlertCircle, CheckCircle2, ChevronLeft } from "lucide-react"
import { CommandList } from "cmdk"
import { cn } from "@/lib/utils"
import { Filter } from "./types"
import ApiClient from "@/lib/apiClient"
import { useState, useEffect, useMemo } from 'react'

interface FilterStatusCommandProps {
  projectId: number
  activeFilters: Filter[]
  onActiveFiltersChange: (filters: Filter[]) => void
  onBack: () => void
}

interface Status {
  id: string;
  name: string;
  color?: string;
}

export function FilterStatusCommand({ 
  projectId, 
  activeFilters, 
  onActiveFiltersChange,
  onBack 
}: FilterStatusCommandProps) {
  const [searchTerm, setSearchTerm] = React.useState("")
  const [isLoadingStatusesData, setIsLoadingStatusesData] = useState(true)
  const [statusesData, setStatusesData] = useState<Status[]>([])
  const apiclient = useMemo(() => ApiClient(), [])

  useEffect(() => {
    const fetchStatuses = async () => {
      try {
        setIsLoadingStatusesData(true)
        const statuses = await apiclient.getIssueStatuses(projectId.toString())
        // Transform the data to ensure id is string
        const transformedStatuses = statuses.map((status: any) => ({
          ...status,
          id: status.id.toString()
        }))
        setStatusesData(transformedStatuses)
      } catch (error) {
        console.error('Error fetching statuses:', error)
      } finally {
        setIsLoadingStatusesData(false)
      }
    }

    fetchStatuses()
  }, [projectId, apiclient])

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
            <h4 className="text-sm font-medium">Status</h4>
            <p className="text-xs text-muted-foreground">Filter by issue status</p>
          </div>
        </div>
      </div>

      {/* Search input - Sticky */}
      <div className="flex-none w-full p-4 pb-2 bg-background/80 backdrop-blur-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50" />
          <input
            type="text"
            placeholder="Search statuses..."
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
            {isLoadingStatusesData ? (
              // Loading state
              <div className="flex flex-col items-center justify-center py-8 space-y-4">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
                <p className="text-sm text-muted-foreground">Loading statuses...</p>
              </div>
            ) : !statusesData?.length ? (
              // Empty state
              <div className="flex flex-col items-center justify-center py-8 space-y-2">
                <AlertCircle className="h-8 w-8 text-muted-foreground/50" />
                <p className="text-sm text-muted-foreground">No statuses found</p>
              </div>
            ) : (
              // Status grid with responsive columns
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {statusesData
                  .filter(status => 
                    status.name.toLowerCase().includes(searchTerm.toLowerCase())
                  )
                  .map((status) => {
                    const isSelected = activeFilters.some(f => f.id === status.id)
                    return (
                      <button
                        key={status.id}
                        onClick={() => {
                          if (isSelected) {
                            onActiveFiltersChange(activeFilters.filter(f => f.id !== status.id))
                          } else {
                            const newFilter = {
                              id: status.id,
                              label: status.name,
                              icon: CheckCircle2
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
                        {/* Status color indicator */}
                        <div className="relative">
                          <div 
                            className={cn(
                              "w-3 h-3 rounded-full",
                              "ring-4 ring-primary/10 group-hover:ring-primary/20 transition-all",
                              isSelected && "ring-primary/30"
                            )}
                            style={{ 
                              backgroundColor: status.color || getStatusColor(status.name)
                            }} 
                          />
                        </div>

                        {/* Status name */}
                        <span className={cn(
                          "text-sm font-medium",
                          isSelected && "text-primary"
                        )}>
                          {status.name}
                        </span>

                        {/* Selected indicator */}
                        {isSelected && (
                          <div 
                            className="h-1.5 w-1.5 rounded-full bg-primary ml-auto"
                            style={{ 
                              backgroundColor: status.color || getStatusColor(status.name)
                            }}
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

// Helper function to get a color based on status name
const getStatusColor = (statusName: string): string => {
  const name = statusName.toLowerCase();
  if (name.includes('done') || name.includes('complete')) return '#2ECC71';
  if (name.includes('progress')) return '#3498DB';
  if (name.includes('block')) return '#E74C3C';
  if (name.includes('review')) return '#F1C40F';
  if (name.includes('todo') || name.includes('open')) return '#95A5A6';
  return '#BDC3C7';
}; 