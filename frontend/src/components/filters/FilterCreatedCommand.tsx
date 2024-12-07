import * as React from "react"
import { Calendar as CalendarIcon, ChevronLeft, X, Clock, Search, Tag, Plus, AlertCircle } from "lucide-react"
import { CommandList } from "cmdk"
import { cn } from "@/lib/utils"
import { BaseFilterCommandProps } from "./types"
import { format, subDays, startOfDay, endOfDay, isEqual } from "date-fns"
import { Calendar } from "@/components/ui/calendar"
import { Button } from "@/components/ui/button"
import { buttonVariants } from "@/components/ui/button"
import { DateRange } from "react-day-picker"

// Predefined date ranges
const DATE_RANGES = [
  {
    id: "today",
    label: "Today",
    getRange: () => ({
      start: startOfDay(new Date()),
      end: endOfDay(new Date())
    })
  },
  {
    id: "yesterday",
    label: "Yesterday",
    getRange: () => ({
      start: startOfDay(subDays(new Date(), 1)),
      end: endOfDay(subDays(new Date(), 1))
    })
  },
  {
    id: "last7days",
    label: "7 days",
    getRange: () => ({
      start: startOfDay(subDays(new Date(), 7)),
      end: endOfDay(new Date())
    })
  },
  {
    id: "last30days",
    label: "30 days",
    getRange: () => ({
      start: startOfDay(subDays(new Date(), 30)),
      end: endOfDay(new Date())
    })
  }
] as const

export function FilterCreatedCommand({ 
  activeFilters, 
  onActiveFiltersChange,
  onBack 
}: BaseFilterCommandProps) {
  const [date, setDate] = React.useState<Date>()
  const [dateRange, setDateRange] = React.useState<DateRange>()
  const [isOpen, setIsOpen] = React.useState(false)
  const [isRangeOpen, setIsRangeOpen] = React.useState(false)
  
  // Filter only created date filters
  const createdFilters = React.useMemo(() => {
    return activeFilters.filter(filter => filter.icon === CalendarIcon)
  }, [activeFilters])

  const handleAddPredefinedRange = (range: typeof DATE_RANGES[number]) => {
    const { start, end } = range.getRange()
    const newFilter = {
      id: range.id,
      label: range.label,
      icon: CalendarIcon,
      metadata: {
        start: start.toISOString(),
        end: end.toISOString()
      }
    }

    // Remove if already exists
    if (createdFilters.some(f => f.id === range.id)) {
      onActiveFiltersChange(activeFilters.filter(f => f.id !== range.id))
      return
    }

    onActiveFiltersChange([...activeFilters, newFilter])
  }

  const handleDateSelect = React.useCallback((selectedDate: Date | undefined) => {
    if (!selectedDate) return
    
    const id = `custom_${selectedDate.toISOString()}`
    
    // Remove if already exists
    if (createdFilters.some(f => f.id === id)) {
      onActiveFiltersChange(activeFilters.filter(f => f.id !== id))
      return
    }

    const newFilter = {
      id,
      label: format(selectedDate, "MMM d, yyyy"),
      icon: CalendarIcon,
      metadata: {
        start: startOfDay(selectedDate).toISOString(),
        end: endOfDay(selectedDate).toISOString()
      }
    }

    setDate(selectedDate)
    onActiveFiltersChange([...activeFilters, newFilter])
    setIsOpen(false)
  }, [activeFilters, createdFilters, onActiveFiltersChange])

  const handleDateRangeSelect = React.useCallback((range: DateRange | undefined) => {
    if (!range?.from) return
    setDateRange(range)
    
    if (!range.to) return // Wait for end date selection
    
    const id = `range_${range.from.toISOString()}_${range.to.toISOString()}`
    
    // Remove if already exists
    if (createdFilters.some(f => f.id === id)) {
      onActiveFiltersChange(activeFilters.filter(f => f.id !== id))
      return
    }

    const newFilter = {
      id,
      label: `${format(range.from, "MMM d")} - ${format(range.to, "MMM d, yyyy")}`,
      icon: CalendarIcon,
      metadata: {
        start: startOfDay(range.from).toISOString(),
        end: endOfDay(range.to).toISOString()
      }
    }

    onActiveFiltersChange([...activeFilters, newFilter])
    setIsRangeOpen(false)
  }, [activeFilters, createdFilters, onActiveFiltersChange])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-none w-full px-3 py-2 border-b border-muted/20">
        <div className="flex items-center gap-2">
          <button
            onClick={onBack}
            className="p-1 -ml-1 hover:bg-muted/10 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div className="flex-1">
            <h4 className="text-sm font-medium leading-none">Created</h4>
            <p className="text-xs text-muted-foreground/70 mt-0.5">Filter by creation date</p>
          </div>
        </div>
      </div>

      <div className="p-2 space-y-3">
        {/* Date Selection Buttons - Enhanced Design */}
        <div className="p-2 space-y-3">
          {/* Main Action Buttons - Connected Design */}
          <div className="flex p-1 gap-px bg-muted/10 rounded-xl">
            <Button
              variant="outline"
              size="sm"
              className={cn(
                "flex-1 justify-center gap-2",
                "h-9 relative overflow-hidden",
                "rounded-xl",
                "border-0",
                "transition-all duration-200",
                isOpen ? [
                  "bg-primary text-primary-foreground",
                  "shadow-lg shadow-primary/20",
                  "hover:bg-primary/90",
                ] : [
                  "bg-transparent hover:bg-muted/10",
                  "text-foreground/70 hover:text-foreground"
                ]
              )}
              onClick={() => {
                setIsOpen(!isOpen)
                setIsRangeOpen(false)
              }}
            >
              <CalendarIcon className="h-4 w-4" />
              <span className="font-medium">Single Date</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              className={cn(
                "flex-1 justify-center gap-2",
                "h-9 relative overflow-hidden",
                "rounded-xl",
                "border-0",
                "transition-all duration-200",
                isRangeOpen ? [
                  "bg-primary text-primary-foreground",
                  "shadow-lg shadow-primary/20",
                  "hover:bg-primary/90",
                ] : [
                  "bg-transparent hover:bg-muted/10",
                  "text-foreground/70 hover:text-foreground"
                ]
              )}
              onClick={() => {
                setIsRangeOpen(!isRangeOpen)
                setIsOpen(false)
              }}
            >
              <CalendarIcon className="h-4 w-4" />
              <span className="font-medium">Date Range</span>
            </Button>
          </div>

          {/* Quick Options - Enhanced Grid */}
          <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4 p-1">
            {DATE_RANGES.map((range) => {
              const isSelected = createdFilters.some(f => f.id === range.id)
              return (
                <button
                  key={range.id}
                  onClick={() => handleAddPredefinedRange(range)}
                  className={cn(
                    "group relative flex items-center justify-center gap-2",
                    "h-9 px-3 rounded-xl",
                    "text-sm font-medium",
                    "transition-all duration-200",
                    "hover:scale-[1.02] active:scale-[0.98]",
                    isSelected ? [
                      "bg-primary text-primary-foreground",
                      "shadow-lg shadow-primary/20",
                      "hover:bg-primary/90"
                    ] : [
                      "bg-muted/5 hover:bg-muted/10",
                      "text-foreground/70 hover:text-foreground",
                      "shadow-sm hover:shadow"
                    ]
                  )}
                >
                  <Clock className="h-3.5 w-3.5" />
                  <span className="relative">
                    {range.label}
                    {isSelected && (
                      <span className="absolute -right-1 -top-1 flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
                      </span>
                    )}
                  </span>
                </button>
              )
            })}
          </div>

          {/* Active Filters - Enhanced Grid */}
          <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 p-1">
            {createdFilters.map((filter) => (
              <button
                key={filter.id}
                onClick={() => onActiveFiltersChange(activeFilters.filter(f => f.id !== filter.id))}
                className={cn(
                  "group relative flex items-center gap-2",
                  "px-3 py-2 rounded-xl text-sm",
                  "bg-muted/5 hover:bg-muted/10",
                  "transition-all duration-200",
                  "hover:scale-[1.02] active:scale-[0.98]"
                )}
              >
                <div className={cn(
                  "relative shrink-0 w-6 h-6 rounded-lg",
                  "flex items-center justify-center",
                  "bg-primary/10 group-hover:bg-primary/20",
                  "transition-all duration-200"
                )}>
                  <CalendarIcon className="h-3.5 w-3.5 text-primaryAccent" />
                </div>

                <div className="flex-1 truncate text-foreground/80">
                  {filter.label}
                </div>

                <div className={cn(
                  "shrink-0 w-6 h-6 rounded-lg",
                  "flex items-center justify-center",
                  "opacity-0 group-hover:opacity-100",
                  "scale-75 group-hover:scale-100",
                  "transition-all duration-200",
                  "bg-red-500/10",
                  "text-red-500"
                )}>
                  <X className="h-3.5 w-3.5" />
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Single Date Calendar */}
      {isOpen && (
        <div className="bg-backgroundSecondary fixed inset-0 z-50">
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="rounded-lg max-h-[400px] overflow-y-auto bg-backgroundSecondary p-6">
              <div className="relative">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsOpen(false)}
                  className="h-8 w-8 p-0 absolute -right-[1.7rem] -top-[2px] z-10 group hover:bg-transparent"
                >
                  <X className="h-4 w-4 transition-colors group-hover:text-primaryAccent" />
                </Button>
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={handleDateSelect}
                  className="rounded-md p-0"
                  classNames={{
                    months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
                    month: "space-y-4",
                    caption: "flex justify-center pt-1 relative items-center",
                    caption_label: "text-sm font-medium",
                    nav: "space-x-1 flex items-center",
                    nav_button: cn(
                      buttonVariants({ variant: "outline" }),
                      "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100"
                    ),
                    nav_button_previous: "absolute left-1",
                    nav_button_next: "absolute right-1",
                    table: "w-full border-collapse space-y-1",
                    head_row: "flex",
                    head_cell: "text-muted-foreground rounded-md w-9 font-normal text-[0.8rem]",
                    row: "flex w-full mt-2",
                    cell: "relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([aria-selected])]:bg-accent [&:has([aria-selected].day-outside)]:bg-accent/50 [&:has([aria-selected].day-range-end)]:rounded-r-md",
                    day: cn(
                      buttonVariants({ variant: "ghost" }),
                      "h-8 w-9 p-0 font-normal aria-selected:opacity-100"
                    ),
                    day_selected: "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground",
                    day_today: "bg-accent text-accent-foreground",
                    day_outside: "text-muted-foreground opacity-50",
                    day_disabled: "text-muted-foreground opacity-50",
                    day_hidden: "invisible",
                    formatters: {
                      formatWeekdayName: (date) => format(date, 'EEE')
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Date Range Calendar */}
      {isRangeOpen && (
        <div className="bg-backgroundSecondary fixed inset-0 z-50">
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="rounded-lg max-h-[400px] overflow-y-auto bg-backgroundSecondary p-6">
              <div className="relative">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsRangeOpen(false)}
                  className="h-8 w-8 p-0 absolute -right-[1.7rem] z-10 group hover:bg-transparent"
                >
                  <X className="h-4 w-4 transition-colors group-hover:text-red-500" />
                </Button>
                <div className="relative">
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 z-20">
                    {dateRange?.from && dateRange?.to && (
                      <Button
                        size="sm"
                        onClick={() => handleDateRangeSelect(dateRange)}
                        className="bg-primary hover:bg-primary/90"
                      >
                        Apply Range
                      </Button>
                    )}
                  </div>
                  
                  <Calendar
                    mode="range"
                    selected={dateRange}
                    onSelect={setDateRange}
                    numberOfMonths={1}
                    className="rounded-md p-0"
                    classNames={{
                      months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
                      month: "space-y-4",
                      caption: "flex justify-center pt-1 relative items-center min-h-[2rem]",
                      caption_label: dateRange?.from && dateRange?.to ? "opacity-0" : "text-sm font-medium",
                      nav: "space-x-1 flex items-center",
                      nav_button: cn(
                        buttonVariants({ variant: "outline" }),
                        "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100"
                      ),
                      nav_button_previous: "absolute left-1",
                      nav_button_next: "absolute right-1",
                      table: "w-full border-collapse space-y-1",
                      head_row: "flex",
                      head_cell: "text-muted-foreground rounded-md w-9 font-normal text-[0.8rem]",
                      row: "flex w-full mt-2",
                      cell: "relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([aria-selected])]:bg-accent [&:has([aria-selected].day-outside)]:bg-accent/50 [&:has([aria-selected].day-range-end)]:rounded-r-md",
                      day: cn(
                        buttonVariants({ variant: "ghost" }),
                        "h-8 w-9 p-0 font-normal aria-selected:opacity-100"
                      ),
                      day_selected: "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground",
                      day_today: "bg-accent text-accent-foreground",
                      day_outside: "text-muted-foreground opacity-50",
                      day_disabled: "text-muted-foreground opacity-50",
                      day_hidden: "invisible",
                      day_range_middle: "aria-selected:bg-accent aria-selected:text-accent-foreground",
                      day_range_end: "aria-selected:bg-primary aria-selected:text-primary-foreground",
                      day_range_start: "aria-selected:bg-primary aria-selected:text-primary-foreground",
                      formatters: {
                        formatWeekdayName: (date) => format(date, 'EEE')
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  )
} 