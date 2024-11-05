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
import { Project } from '@/types/project'

interface ProjectSelectorProps {
  projects: Project[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onAddNewProject: () => void;
}

export default function ProjectSelector({ 
  projects = [],
  selectedProjectId, 
  onSelectProject, 
  onAddNewProject
}: ProjectSelectorProps) {
  const [isInitialLoading, setIsInitialLoading] = React.useState(true);
  const [isLoading, setIsLoading] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [isOpen, setIsOpen] = React.useState(false);

  React.useEffect(() => {
    if (projects?.length > 0 && !selectedProjectId) {
      onSelectProject(projects[0].id);
    }
    setTimeout(() => setIsInitialLoading(false), 100);
  }, [projects, selectedProjectId, onSelectProject]);

  const selectedProject = projects?.find(project => project.id === selectedProjectId);

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

  const filteredProjects = projects?.filter((project) =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 px-2 text-xs"
        >
          <div className="flex items-center gap-2">
            <div className="max-w-[100px] truncate">
              {isLoading || isInitialLoading ? (
                <div className="h-3 w-16 bg-muted/30 animate-pulse rounded-sm" />
              ) : !projects?.length ? (
                <span>No Projects</span>
              ) : (
                <span className="hidden md:inline">{selectedProject?.name}</span>
              )}
            </div>
            <ChevronDown className="h-3 w-3 opacity-50" />
          </div>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-[300px]"
        align="start"
        alignOffset={-5}
        sideOffset={5}
        side="top"
      >
        <div className="p-2">
          <Input
            type="text"
            placeholder="Search projects..."
            value={searchTerm}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
            className="w-full"
          />
        </div>
        {filteredProjects.length > 0 ? (
          <>
            <DropdownMenuLabel>Projects</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {filteredProjects.map((project) => (
              <DropdownMenuItem
                key={project.id}
                onSelect={() => handleSelectProject(project.id)}
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
          </>
        ) : (
          <div className="py-4 px-2 text-sm text-muted-foreground">No projects found</div>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={handleAddNewProject}>
          <PlusCircle className="mr-2 h-4 w-4" />
          Add New Project
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
