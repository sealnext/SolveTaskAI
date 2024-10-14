import React from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RefreshCw, Plus, Trash2 } from 'lucide-react';
import SafeImage from '@/components/SafeImage';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { ExternalProjectSchema, Project } from '@/lib/types';

interface ExternalProjectsListProps {
  externalProjects: ExternalProjectSchema[];
  projects: Project[];
  isLoading: boolean;
  newlyAddedProjects: Set<string>;
  onAddInternalProject: (project: ExternalProjectSchema) => void;
  onReloadEmbeddings: (project: ExternalProjectSchema) => void;
  onDeleteProject: (project: ExternalProjectSchema) => void;
}

const ExternalProjectsList: React.FC<ExternalProjectsListProps> = ({
  externalProjects,
  projects,
  isLoading,
  newlyAddedProjects,
  onAddInternalProject,
  onReloadEmbeddings,
  onDeleteProject
}) => {
  const isProjectAlreadyAdded = (externalProject: ExternalProjectSchema) => {
    return projects.some(internalProject => 
      internalProject.key === externalProject.key || 
      internalProject.name === externalProject.name
    );
  };

  const renderProjectItem = (project: ExternalProjectSchema) => {
    const isAdded = isProjectAlreadyAdded(project);
    const isNewlyAdded = newlyAddedProjects.has(project.id);
    
    return (
      <li 
        key={project.id} 
        className={`flex items-center justify-between p-2 rounded-md ${
          isAdded || isNewlyAdded || project.isDeleted ? 'bg-muted' : 'bg-card'
        }`}
      >
        <div className="flex items-center space-x-2">
          <SafeImage 
            src={project.avatarUrl} 
            alt={project.name} 
            width={24}
            height={24} 
            className="w-6 h-6 rounded" 
          />
          <span>{project.name}</span>
          <span className="text-sm text-muted-foreground">({project.key})</span>
        </div>
        {project.isDeleted ? (
          <Badge variant="destructive">Deleted</Badge>
        ) : isNewlyAdded ? (
          <Badge variant="secondary">Added</Badge>
        ) : isAdded ? (
          <div className="flex space-x-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => onReloadEmbeddings(project)}
                    disabled={isLoading}
                    className="rounded-full group"
                  >
                    <RefreshCw className="w-4 h-4 group-hover:text-primary-foreground" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Reload Embeddings</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <AlertDialog>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <AlertDialogTrigger asChild>
                      <Button size="icon" variant="ghost" className="rounded-full group">
                        <Trash2 className="w-4 h-4 text-destructive group-hover:text-destructive-foreground" />
                      </Button>
                    </AlertDialogTrigger>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Delete Project</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete the project
                    and remove all associated data.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={() => onDeleteProject(project)}>
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        ) : (
          <Button
            size="sm"
            onClick={() => onAddInternalProject(project)}
            disabled={isLoading}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add
          </Button>
        )}
      </li>
    );
  };

  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold mb-2">External Projects:</h3>
      <ScrollArea className="h-[200px]">
        <ul className="space-y-2">
          {externalProjects.map(renderProjectItem)}
        </ul>
      </ScrollArea>
    </div>
  );
};

export default ExternalProjectsList;
