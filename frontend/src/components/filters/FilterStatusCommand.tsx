import * as React from "react"
import { Search, AlertCircle, CheckCircle2, ChevronLeft } from "lucide-react"
import { CommandList } from "../ui/command"
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
  id: number;
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
        setStatusesData(statuses)
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
      <div className="w-full p-1 border-b border-muted/30">
        <div className="flex items-center gap-2 px-2 py-1">
          <button
            onClick={onBack}
            className="p-1 hover:bg-muted/10 rounded-md transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="text-sm font-medium">Status</span>
        </div>
      </div>

      {/* Filter Content */}
      <CommandList className="w-full max-h-[400px] overflow-y-auto">
        <div className="p-4">
          {/* Search for statuses */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50" />
            <input
              type="text"
              placeholder="Search statuses..."
              className="w-full pl-9 pr-4 py-2 text-sm bg-muted/10 hover:bg-muted/20 focus:bg-muted/20 
                      rounded-xl border border-muted/20 focus:border-primary/20 outline-none
                      transition-all duration-150 ease-in-out"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {isLoadingStatusesData ? (
            // Elegant loading state
            <div className="flex flex-col items-center justify-center h-48 space-y-4">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
              <p className="text-sm text-muted-foreground">Loading statuses...</p>
            </div>
          ) : !statusesData?.length ? (
            // Empty state
            <div className="flex flex-col items-center justify-center h-48 space-y-2">
              <AlertCircle className="h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">No statuses found</p>
            </div>
          ) : (
            // Status grid with filtered results
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {statusesData
                .filter(status => 
                  status.name.toLowerCase().includes(searchTerm.toLowerCase())
                )
                .map((status) => {
                  const isSelected = activeFilters.some(f => f.id === status.id);
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
                          };
                          onActiveFiltersChange([...activeFilters, newFilter])
                        }
                      }}
                      className={cn(
                        "group relative flex items-center gap-3 p-3 rounded-xl transition-all duration-150",
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
                        <CheckCircle2 className="absolute right-3 h-4 w-4 text-primary" />
                      )}
                    </button>
                  );
                })}
            </div>
          )}
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