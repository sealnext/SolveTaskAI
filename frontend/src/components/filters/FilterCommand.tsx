import * as React from "react"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandList,
  CommandItem,
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
import { FilterSprintCommand } from "./FilterSprintCommand"
import { FilterAssigneeCommand } from "./FilterAssigneeCommand"
import { FilterReporterCommand } from "./FilterReporterCommand"
import { FilterCreatedCommand } from "./FilterCreatedCommand"
import { FilterResolvedCommand } from "./FilterResolvedCommand"

interface FilterCommandProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  activeFilters: Filter[]
  onActiveFiltersChange: (filters: Filter[]) => void
  projectId: number
}

const quickFilters: Filter[] = [
  { id: 'my-tickets', label: 'Assigned to me', icon: User },
  { id: 'unresolved', label: 'Unresolved', icon: AlertCircle},
  { id: 'critical', label: 'Highest Priority', icon: AlertCircle},
  { id: 'blocked', label: 'Blocked', icon: XCircle},
  { id: 'due-today', label: 'Due Today', icon: Calendar},
  { id: 'overdue', label: 'Overdue', icon: Clock},
  { id: 'in-progress', label: 'In Progress', icon: Timer},
  { id: 'needs-review', label: 'Needs Review', icon: Search},
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
      { id: 'resolved', label: 'Resolved', icon: Clock }
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

  // Filter function for both quick filters and meta tags
  const filterItems = (items: Filter[], term: string) => {
    if (!term) return items
    return items.filter(item => 
      item.label.toLowerCase().includes(term.toLowerCase())
    )
  }

  // Filter meta tags groups
  const filterMetaTags = (groups: FilterGroup[], term: string) => {
    if (!term) return groups
    return groups.map(group => ({
      ...group,
      items: group.items.filter(item =>
        item.label.toLowerCase().includes(term.toLowerCase()) ||
        group.group.toLowerCase().includes(term.toLowerCase())
      )
    })).filter(group => group.items.length > 0)
  }

  const filteredQuickFilters = filterItems(quickFilters, searchTerm)
  const filteredMetaTags = filterMetaTags(metaTags, searchTerm)

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
    <Command className="w-full" shouldFilter={false}>
      {/* Header with search */}
      <div className="w-full">
        <CommandInput 
          placeholder="Search filters..."
          value={searchTerm}
          onValueChange={setSearchTerm}
          className="w-full px-4 py-3 text-sm bg-transparent hover:bg-muted/10 focus:bg-muted/10 
                    border-0 border-b border-muted/30 rounded-none
                    ring-0 ring-offset-0 ring-accent/20 
                    placeholder:text-muted-foreground/50 text-foreground outline-none focus:outline-none
                    transition-all duration-150 ease-in-out"
        />
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
        {filteredQuickFilters.length === 0 && filteredMetaTags.length === 0 && (
          <CommandEmpty>No filters found.</CommandEmpty>
        )}
        
        {/* Quick Filters */}
        {filteredQuickFilters.length > 0 && (
          <CommandGroup heading="Quick Filters">
            <div className="w-full flex flex-wrap items-center gap-1 p-1.5 px-2">
              {filteredQuickFilters.map(filter => (
                <CommandItem
                  key={filter.id}
                  onSelect={() => handleQuickFilter(filter)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <filter.icon className="h-3.5 w-3.5 text-primary" />
                  <span className="text-foreground">{filter.label}</span>
                  {filter.count && (
                    <span className="text-muted-foreground">({filter.count})</span>
                  )}
                </CommandItem>
              ))}
            </div>
          </CommandGroup>
        )}

        {/* Complex Filters */}
        {filteredMetaTags.length > 0 && (
          <div className="w-full grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 px-2">
            {filteredMetaTags.map(group => (
              <CommandGroup key={group.group} heading={group.group}>
                {group.items.map(item => (
                  <CommandItem
                    key={item.id}
                    onSelect={() => setSelectedFilter(item)}
                    className="w-full flex items-center gap-2 px-2.5 py-1.5 text-sm rounded-lg
                      text-left hover:bg-muted/20 transition-colors"
                  >
                    <item.icon className="h-3.5 w-3.5 text-primary" />
                    <span>{item.label}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </div>
        )}
      </CommandList>
    </Command>
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
        ) : selectedFilter?.id === 'sprint' ? (
          <FilterSprintCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : selectedFilter?.id === 'assignee' ? (
          <FilterAssigneeCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : selectedFilter?.id === 'reporter' ? (
          <FilterReporterCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : selectedFilter?.id === 'created' ? (
          <FilterCreatedCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : selectedFilter?.id === 'resolved' ? (
          <FilterResolvedCommand
            projectId={projectId}
            activeFilters={activeFilters}
            onActiveFiltersChange={onActiveFiltersChange}
            onBack={() => setSelectedFilter(null)}
          />
        ) : renderMainScreen()}
      </CommandDialog>
    </div>
  )
} 