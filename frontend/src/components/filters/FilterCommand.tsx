import * as React from "react"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandList,
} from "@/components/ui/command"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  Tag, 
  AlertCircle, 
  Clock, 
  User, 
  Calendar,
  MessageSquare,
  CheckCircle2,
  Type,
  Flag,
  X,
  Search,
  Timer,
  XCircle,
} from "lucide-react"
import { Filter, FilterGroup } from "./types"
import { FilterStatusCommand } from "./FilterStatusCommand"
import { FilterLabelsCommand } from "./FilterLabelsCommand"
import { FilterPriorityCommand } from "./FilterPriorityCommand"
import { FilterIssueTypeCommand } from "./FilterIssueTypeCommand"
import { CommandDialog } from "@/components/ui/command-dialog"

interface FilterCommandProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  activeFilters: Filter[]
  onActiveFiltersChange: (filters: Filter[]) => void
  projectId: number
}

const quickFilters: Filter[] = [
  { id: 'my-tickets', label: 'Assigned to me', icon: User, count: 12 },
  { id: 'unresolved', label: 'Unresolved', icon: AlertCircle, count: 8 },
  { id: 'critical', label: 'Critical Priority', icon: AlertCircle, count: 3 },
  { id: 'blocked', label: 'Blocked', icon: XCircle, count: 3 },
  { id: 'due-today', label: 'Due Today', icon: Calendar, count: 2 },
  { id: 'overdue', label: 'Overdue', icon: Clock, count: 5 },
  { id: 'in-progress', label: 'In Progress', icon: Timer, count: 6 },
  { id: 'needs-review', label: 'Needs Review', icon: Search, count: 4 },
]

const metaTags: FilterGroup[] = [
  {
    group: "Status",
    items: [
      { id: 'status', label: 'Status', icon: CheckCircle2, options: ['Open', 'In Progress', 'Resolved', 'Closed'] },
      { id: 'priority', label: 'Priority', icon: Flag, options: ['Critical', 'High', 'Medium', 'Low'] }
    ]
  },
  {
    group: "Type",
    items: [
      { id: 'labels', label: 'Labels', icon: Tag, isMulti: true },
      { id: 'issue_type', label: 'Issue Type', icon: Type, options: ['Bug', 'Task', 'Story', 'Epic'] },
      { id: 'sprint', label: 'Sprint', icon: Timer }
    ]
  },
  {
    group: "People",
    items: [
      { id: 'assignee', label: 'Assignee', icon: User },
      { id: 'reporter', label: 'Reporter', icon: MessageSquare }
    ]
  },
  {
    group: "Time",
    items: [
      { id: 'created', label: 'Created', icon: Calendar },
      { id: 'resolutiondate', label: 'Resolved', icon: Clock }
    ]
  }
]

export function FilterCommand({ 
  open, 
  onOpenChange, 
  activeFilters, 
  onActiveFiltersChange, 
  projectId 
}: FilterCommandProps) {
  const [searchTerm, setSearchTerm] = React.useState("")
  const [selectedFilter, setSelectedFilter] = React.useState<Filter | null>(null)
  const ref = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (target.closest('[data-filter-trigger="true"]')) {
        return;
      }
      
      if (ref.current && !ref.current.contains(target)) {
        onOpenChange(false)
      }
    }

    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open, onOpenChange])

  const handleQuickFilter = (filter: Filter) => {
    if (!activeFilters.find(f => f.id === filter.id)) {
      onActiveFiltersChange([...activeFilters, filter])
    }
  }

  const removeFilter = (filterId: string) => {
    onActiveFiltersChange(activeFilters.filter(f => f.id !== filterId))
  }

  const renderMainScreen = () => (
    <>
      {/* Header with search */}
      <div className="w-full p-1">
        <div className="relative flex items-center w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50 z-10" />
          <div className="w-full">
            <CommandInput 
              placeholder="Search filters..."
              value={searchTerm}
              onValueChange={setSearchTerm}
              className="w-full pl-9 pr-4 py-2 text-sm bg-muted/10 hover:bg-muted/20 focus:bg-muted/20 
                        rounded-xl border-0 ring-0 ring-offset-0 ring-accent/20 
                        placeholder:text-muted-foreground/50 text-foreground outline-none focus:outline-none
                        transition-all duration-150 ease-in-out"
            />
          </div>
        </div>
      </div>

      {/* Active filters */}
      {activeFilters.length > 0 && (
        <div className="w-full flex items-center gap-1 p-1.5 px-2 border-b border-muted/30 bg-muted/5">
          <Button 
            variant="ghost" 
            size="sm" 
            className="text-xs h-5 px-2 hover:bg-muted/10 flex-shrink-0"
            onClick={() => onActiveFiltersChange([])}
          >
            Clear
          </Button>
          <div className="flex items-center gap-1 overflow-x-auto
            [&::-webkit-scrollbar]:h-1.5
            [&::-webkit-scrollbar-track]:bg-muted/5
            [&::-webkit-scrollbar-thumb]:bg-muted/40
            [&::-webkit-scrollbar-thumb]:hover:bg-muted/60
            [&::-webkit-scrollbar-thumb]:rounded-full
            [&::-webkit-scrollbar-track]:rounded-full
            dark:[&::-webkit-scrollbar-track]:bg-muted/5
            dark:[&::-webkit-scrollbar-thumb]:bg-white/20
            dark:[&::-webkit-scrollbar-thumb]:hover:bg-white/30
            scrollbar
            scrollbar-track-rounded-full
            scrollbar-thumb-rounded-full
            scrollbar-track-muted/5
            scrollbar-thumb-muted/40
            hover:scrollbar-thumb-muted/60
            dark:scrollbar-thumb-white/20
            dark:hover:scrollbar-thumb-white/30
            px-0.5
            py-2"
          >
            {activeFilters.map(filter => (
              <Badge 
                key={filter.id} 
                variant="secondary" 
                className="flex items-center gap-1 whitespace-nowrap py-0.5 text-xs bg-muted/10"
              >
                {filter.icon && <filter.icon className="h-3 w-3" />}
                {filter.label}
                <button
                  onClick={() => removeFilter(filter.id)}
                  className="ml-1 hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>
      )}

      <CommandList className="w-full max-h-[300px] overflow-y-auto">
        {/* Quick Filters */}
        <CommandGroup heading="Quick Filters" className="w-full pb-2">
          <div className="w-full flex flex-wrap items-center gap-1 p-1.5 px-2">
            {quickFilters.map(filter => (
              <button
                key={filter.id}
                onClick={() => handleQuickFilter(filter)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg hover:bg-muted/50 transition-colors"
              >
                <filter.icon className="h-3.5 w-3.5 text-primary" />
                <span className="text-foreground">{filter.label}</span>
                {filter.count && (
                  <span className="text-muted-foreground">({filter.count})</span>
                )}
              </button>
            ))}
          </div>
        </CommandGroup>

        {/* Complex Filters */}
        <div className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 px-2">
          {metaTags.map(group => (
            <CommandGroup key={group.group} heading={group.group} className="w-full py-2">
              {group.items.map(item => (
                <button
                  key={item.id}
                  onClick={() => setSelectedFilter(item)}
                  className="w-full flex items-center gap-2 px-2.5 py-1.5 text-sm rounded-lg
                    text-left hover:bg-muted/20 transition-colors"
                >
                  <item.icon className="h-3.5 w-3.5 text-primary" />
                  <span>{item.label}</span>
                </button>
              ))}
            </CommandGroup>
          ))}
        </div>
      </CommandList>
    </>
  )

  if (!open) return null

  return (
    <div ref={ref}>
      <CommandDialog>
        {selectedFilter?.id === 'status' ? (
          <FilterStatusCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : selectedFilter?.id === 'labels' ? (
          <FilterLabelsCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : selectedFilter?.id === 'priority' ? (
          <FilterPriorityCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : selectedFilter?.id === 'issue_type' ? (
          <FilterIssueTypeCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : (
          renderMainScreen()
        )}
      </CommandDialog>
    </div>
  )
} 