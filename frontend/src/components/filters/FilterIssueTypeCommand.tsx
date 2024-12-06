import * as React from "react"
import { Search, Type, ChevronLeft } from "lucide-react"
import { CommandList } from "cmdk"
import { cn } from "@/lib/utils"
import { BaseFilterCommandProps } from "./types"
import ApiClient from "@/lib/apiClient"
import Image from "next/image"

interface IssueType {
  id: string;
  name: string;
  iconUrl: string;
  description: string;
  subtask: boolean;
  hierarchyLevel: number;
}

export function FilterIssueTypeCommand({ 
  projectId, 
  activeFilters, 
  onActiveFiltersChange,
  onBack 
}: BaseFilterCommandProps) {
  const [searchTerm, setSearchTerm] = React.useState("")
  const [isLoadingTypes, setIsLoadingTypes] = React.useState(true)
  const [issueTypes, setIssueTypes] = React.useState<IssueType[]>([])
  const apiclient = React.useMemo(() => ApiClient(), [])

  React.useEffect(() => {
    const fetchIssueTypes = async () => {
      try {
        setIsLoadingTypes(true)
        // TODO: Replace with actual API call when ready
        // const data = await apiclient.getIssueTypes(projectId.toString())
        const data = [
          {
            "self": "https://sealnext.atlassian.net/rest/api/2/issuetype/10010",
            "id": "10010",
            "description": "Tasks track small, distinct pieces of work.",
            "iconUrl": "https://sealnext.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10318?size=medium",
            "name": "Task",
            "untranslatedName": "Task",
            "subtask": false,
            "hierarchyLevel": 0,
            "scope": {
            "type": "PROJECT",
            "project": {
                "id": "10002"
            }
            }
        },
        {
            "self": "https://sealnext.atlassian.net/rest/api/2/issuetype/10011",
            "id": "10011",
            "description": "Epics track collections of related bugs, stories, and tasks.",
            "iconUrl": "https://sealnext.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10307?size=medium",
            "name": "Epic",
            "untranslatedName": "Epic",
            "subtask": false,
            "hierarchyLevel": 1,
            "scope": {
            "type": "PROJECT",
            "project": {
                "id": "10002"
            }
            }
        },
        {
            "self": "https://sealnext.atlassian.net/rest/api/2/issuetype/10012",
            "id": "10012",
            "description": "Subtasks track small pieces of work that are part of a larger task.",
            "iconUrl": "https://sealnext.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10316?size=medium",
            "name": "Subtask",
            "untranslatedName": "Subtask",
            "subtask": true,
            "hierarchyLevel": -1,
            "scope": {
            "type": "PROJECT",
            "project": {
                "id": "10002"
            }
            }
        }
        ]
        // Transform the data to ensure id is string
        const transformedTypes = data.map((type: any) => ({
          id: type.id.toString(),
          name: type.name,
          iconUrl: type.iconUrl,
          description: type.description,
          subtask: type.subtask,
          hierarchyLevel: type.hierarchyLevel
        }))
        setIssueTypes(transformedTypes)
      } catch (error) {
        console.error('Error fetching issue types:', error)
      } finally {
        setIsLoadingTypes(false)
      }
    }

    fetchIssueTypes()
  }, [projectId, apiclient])

  // Filter issue types based on search term
  const filteredTypes = React.useMemo(() => {
    if (!searchTerm) return issueTypes
    const normalized = searchTerm.toLowerCase()
    return issueTypes.filter(type => 
      type.name.toLowerCase().includes(normalized) ||
      type.description.toLowerCase().includes(normalized)
    )
  }, [issueTypes, searchTerm])

  // Group issue types by hierarchy level
  const groupedTypes = React.useMemo(() => {
    const groups = filteredTypes.reduce((acc, type) => {
      const level = type.hierarchyLevel;
      const groupName = level === 1 ? "Epics" : 
                       level === 0 ? "Standard Issues" : 
                       level === -1 ? "Subtasks" : "Other";
      
      if (!acc[groupName]) {
        acc[groupName] = [];
      }
      acc[groupName].push(type);
      return acc;
    }, {} as Record<string, IssueType[]>);

    // Sort groups in specific order
    const orderedGroups: Record<string, IssueType[]> = {};
    ["Epics", "Standard Issues", "Subtasks", "Other"].forEach(key => {
      if (groups[key]?.length > 0) {
        orderedGroups[key] = groups[key];
      }
    });

    return orderedGroups;
  }, [filteredTypes]);

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
            <h4 className="text-sm font-medium">Issue Type</h4>
            <p className="text-xs text-muted-foreground">Filter by issue type</p>
          </div>
        </div>
      </div>

      {/* Search input - Sticky */}
      <div className="flex-none w-full p-4 pb-2 bg-background/80 backdrop-blur-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50" />
          <input
            type="text"
            placeholder="Search issue types..."
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
          {isLoadingTypes ? (
            // Loading state
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
              <p className="text-sm text-muted-foreground">Loading issue types...</p>
            </div>
          ) : filteredTypes.length === 0 ? (
            // Empty state
            <div className="flex flex-col items-center justify-center py-8 space-y-2">
              <Type className="h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">No issue types found</p>
            </div>
          ) : (
            // Issue types grid
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(groupedTypes).map(([groupName, types]) => (
                <React.Fragment key={groupName}>
                  {/* Issue type items */}
                  {types.map((type) => {
                    const isSelected = activeFilters.some(f => f.id === type.id)
                    return (
                      <button
                        key={type.id}
                        onClick={() => {
                          if (isSelected) {
                            onActiveFiltersChange(activeFilters.filter(f => f.id !== type.id))
                          } else {
                            const newFilter = {
                              id: type.id,
                              label: type.name,
                              icon: Type
                            }
                            onActiveFiltersChange([...activeFilters, newFilter])
                          }
                        }}
                        className={cn(
                          "group relative w-full flex items-start gap-2.5 px-2.5 py-1.5 rounded-lg",
                          "hover:bg-muted/10",
                          "border border-transparent",
                          isSelected && "bg-primary/5 border-primary/20"
                        )}
                      >
                        {/* Issue type icon */}
                        <div 
                          className={cn(
                            "relative shrink-0 w-5 h-5 rounded-md mt-0.5",
                            "flex items-center justify-center",
                            "bg-gradient-to-b from-white/10 to-white/5",
                            "ring-1 ring-white/20"
                          )}
                        >
                          <Image 
                            src={type.iconUrl} 
                            alt={type.name}
                            width={14}
                            height={14}
                            className="opacity-90"
                          />
                        </div>

                        {/* Issue type details */}
                        <div className="flex flex-col min-w-0 flex-1">
                          <div className={cn(
                            "text-sm font-medium truncate",
                            isSelected && "text-primary"
                          )}>
                            {type.name}
                          </div>
                          <div className="text-xs text-muted-foreground/70 line-clamp-1">
                            {type.description}
                          </div>
                        </div>

                        {/* Selected indicator */}
                        {isSelected && (
                          <div className="h-1.5 w-1.5 rounded-full bg-primary shrink-0 mt-1.5" />
                        )}
                      </button>
                    )
                  })}
                </React.Fragment>
              ))}
            </div>
          )}
        </div>
      </CommandList>
    </>
  )
} 