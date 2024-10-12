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

interface Project {
  id: number;
  name: string;
  service_type: string;
  company_id: number;
  domain: string;
}

interface ProjectSelectorProps {
  projects: Project[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
}

export default function ProjectSelector({ projects, selectedProjectId, onSelectProject }: ProjectSelectorProps) {
  const selectedProject = projects.find(project => project.id === selectedProjectId);

  const handleSelectProject = (projectId: number) => {
    onSelectProject(projectId);
  }

  const handleAddNewProject = () => {
    // Implement the logic to add a new project here
    console.log(projects)
    console.log("Add new project");
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="w-full h-full bg-backgroundSecondary bg-opacity-80 backdrop-filter backdrop-blur-md text-foreground rounded-2xl px-6 flex items-center justify-between space-x-2 shadow-lg border-muted border-2 transition-all duration-300 hover:bg-opacity-100 focus:outline-none">
          <span className="truncate text-sm text-foreground placeholder-foreground-secondary">
            {selectedProject ? selectedProject.name : "Select Project"}
          </span>
          <ChevronDown className="h-4 w-4 flex-shrink-0 transition-transform duration-200 data-[state=open]:rotate-180" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        className="w-[200px] bg-backgroundSecondary bg-opacity-90 backdrop-filter backdrop-blur-md border-muted border-2 rounded-xl shadow-lg"
        align="end"
      >
        <DropdownMenuLabel className="text-foreground">Projects</DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-muted" />
        {projects.map((project) => (
          <DropdownMenuItem
            key={project.id}
            onSelect={() => handleSelectProject(project.id)}
            className="text-foreground hover:bg-muted-20 active:bg-muted transition-colors focus:bg-muted-20 focus:outline-none p-3 group rounded-lg"
          >
            <div className="flex flex-col">
              <div className="flex items-center mt-1">
                <span className="font-semibold text-lg mr-2">{project.name}</span>
                <span className="text-sm text-muted-foreground bg-muted px-2 py-1 rounded-full transition-colors duration-200 group-hover:bg-muted group-hover:bg-opacity-30 group-hover:text-foreground">
                  {project.service_type}
                </span>
              </div>
              <span className="text-sm text-blue-500">
                {project.domain.replace(/^https?:\/\//, '').replace(/\/$/, '')}
              </span>
            </div>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator className="bg-muted" />
        <DropdownMenuItem 
          onSelect={handleAddNewProject}
          className="text-foreground hover:bg-muted-20 active:bg-muted-20 transition-colors focus:bg-muted-20 focus:outline-none rounded-lg"
        >
          <PlusCircle className="mr-2 h-4 w-4" />
          <span>Add New Project</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
