import * as React from "react"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "./ui/command"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { 
  Tag, 
  AlertCircle, 
  Clock, 
  User, 
  Calendar,
  MessageSquare,
  CheckCircle2,
  Hash,
  Flag,
  Bookmark,
  X,
  Search,
  Plus,
  Timer,
  Type,
  CheckSquare,
  XCircle
} from "lucide-react"

interface FilterCommandProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface Filter {
  id: string
  label: string
  icon: React.ElementType
  count?: number
  options?: string[]
  isMulti?: boolean
}

interface FilterGroup {
  group: string
  items: Filter[]
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
      { id: 'resolution', label: 'Resolution', icon: CheckSquare, options: ['Done', 'Won\'t Do', 'Duplicate', 'Cannot Reproduce'] },
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

export function FilterCommand({ open, onOpenChange }: FilterCommandProps) {
  const [searchTerm, setSearchTerm] = React.useState("")
  const [activeFilters, setActiveFilters] = React.useState<Filter[]>([])
  const ref = React.useRef<HTMLDivElement>(null)

  const handleQuickFilter = (filter: Filter) => {
    if (!activeFilters.find(f => f.id === filter.id)) {
      setActiveFilters([...activeFilters, filter])
    }
  }

  const removeFilter = (filterId: string) => {
    setActiveFilters(activeFilters.filter(f => f.id !== filterId))
  }

  return (
    <div ref={ref} className="absolute bottom-full left-0 right-0 mb-4 w-full">
      <Command className="w-full rounded-2xl border-2 border-muted overflow-hidden bg-backgroundSecondary bg-opacity-80 backdrop-filter backdrop-blur-md shadow-lg">
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
                          transition-all duration-150 ease-in-out data-[cmdk-input]:w-full"
              />
            </div>
          </div>
        </div>

        {/* Active filters */}
        {activeFilters.length > 0 && (
          <div className="w-full flex items-center gap-1 p-1.5 px-2 border-b border-muted/30 bg-muted/5 overflow-x-auto">
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
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-xs h-5 px-2 ml-1 hover:bg-muted/10"
              onClick={() => setActiveFilters([])}
            >
              Clear
            </Button>
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

          {/* Meta Tags */}
          <div className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 px-2">
            {metaTags.map(group => (
              <CommandGroup key={group.group} heading={group.group} className="w-full py-2">
                {group.items.map(item => (
                  <CommandItem 
                    key={item.id}
                    className="w-full flex items-center gap-2 px-2 py-1.5 text-sm"
                    onSelect={() => handleQuickFilter(item)}
                  >
                    <item.icon className="h-3.5 w-3.5 text-primary" />
                    <span>{item.label}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </div>

          {searchTerm && (
            <CommandGroup heading="Search Results" className="w-full">
              <CommandEmpty>No filters found.</CommandEmpty>
              {/* Filter results will be rendered here */}
            </CommandGroup>
          )}
        </CommandList>
      </Command>
    </div>
  )
} 