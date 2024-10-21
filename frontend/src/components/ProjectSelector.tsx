'use client'

import * as React from "react"
import { PlusCircle, ChevronDown } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface Project {
  id: number;
  name: string;
  service_type: string;
  domain: string;
}

interface ProjectSelectorProps {
  projects: Project[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onAddNewProject: () => void;
}

export default function ProjectSelector({ 
  projects, 
  selectedProjectId, 
  onSelectProject, 
  onAddNewProject
}: ProjectSelectorProps) {
  const selectedProject = projects.find(project => project.id === selectedProjectId);
  const [isLoading, setIsLoading] = React.useState(false)
  const [searchTerm, setSearchTerm] = React.useState('')
  const handleSelectProject = (projectId: number) => {
    setIsLoading(true);
    onSelectProject(projectId);
    setIsLoading(false);
  }

  const filteredProjects = projects.filter((project) =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase())
  )


  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="lg"
          className="w-full justify-between"
          aria-label="Select Project"
        >
          {isLoading ? (
            <div className="h-5 w-32 bg-muted animate-pulse rounded"></div>
          ) : (
            <span className="truncate">
              {selectedProject ? selectedProject.name : "Select Project"}
            </span>
          )}
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-[300px]"
        align="start"
        alignOffset={-5}
        sideOffset={5}
        side="top"
        key="dropdown-content"
      >
        <div className="p-2">
          <Input
            type="text"
            placeholder="Search projects..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full"
          />
        </div>
        {filteredProjects.length > 0 ? (
          <div key="project-list">
            <DropdownMenuLabel key="projects-label">Projects</DropdownMenuLabel>
            <DropdownMenuSeparator key="projects-separator" />
            {filteredProjects.map((project) => (
              <DropdownMenuItem
                key={`project-${project.id}`}
                onSelect={() => handleSelectProject(project.id)}
                className="w-full p-0"
              >
                <div className="flex flex-col py-2 px-3 w-full">
                  <div className="flex items-center justify-between w-full">
                    <span className="font-medium">
                      {project.name}
                    </span>
                    <span className="text-xs text-muted-foreground bg-secondary px-2 py-1 rounded-full">
                      {project.service_type}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {project.domain.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                  </span>
                </div>
              </DropdownMenuItem>
            ))}
          </div>
        ) : (
          <div key="no-projects" className="py-4 px-2 text-sm text-muted-foreground">No projects found</div>
        )}
        <DropdownMenuSeparator key="add-project-separator" />
        <div key="add-project-button">
          <Button 
            onClick={onAddNewProject} 
            variant="ghost" 
            className="w-full justify-start pl-2"
          >
            <PlusCircle className="mr-2 h-4 w-4" />
            Add New Project
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
