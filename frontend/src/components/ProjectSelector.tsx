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
  const [isInitialLoading, setIsInitialLoading] = React.useState(true);
  const [isLoading, setIsLoading] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [isOpen, setIsOpen] = React.useState(false);

  React.useEffect(() => {
    if (projects.length > 0 && !selectedProjectId) {
      onSelectProject(projects[0].id);
    }
    // Simulăm un mic delay pentru a evita flash-ul de "No Projects Available"
    setTimeout(() => setIsInitialLoading(false), 100);
  }, [projects, selectedProjectId, onSelectProject]);

  const selectedProject = projects.find(project => project.id === selectedProjectId);

  const handleSelectProject = (projectId: number) => {
    setIsLoading(true);
    onSelectProject(projectId);
    setIsLoading(false);
    setIsOpen(false);
  }

  const handleAddNewProject = () => {
    setIsOpen(false);
    onAddNewProject();
  }

  const filteredProjects = projects.filter((project) =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="lg"
          className="w-full justify-between"
          aria-label="Select Project"
        >
          <div className="w-[100px] flex items-center">
            {isLoading || isInitialLoading ? (
              <div className="flex items-center gap-1.5">
                <div className="h-3 w-20 bg-muted/30 animate-pulse rounded-sm"></div>
                <div className="h-3 w-8 bg-muted/20 animate-pulse rounded-sm"></div>
              </div>
            ) : projects.length === 0 ? (
              <span className="truncate">No Projects Available</span>
            ) : (
              <span className="truncate">
                {selectedProject?.name}
              </span>
            )}
          </div>
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
            onClick={handleAddNewProject} 
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
