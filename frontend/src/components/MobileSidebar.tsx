'use client'

import * as React from "react"
import { X, PenSquare } from "lucide-react"
import { cn } from "@/lib/utils"
import { Project } from "@/types/project"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarTrigger,
  SidebarProvider,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarGroup,
  SidebarGroupContent,
  useSidebar,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"

interface MobileSidebarProps {
  projects: Project[]
  selectedProjectId: number | null
  onSelectProject: (projectId: number) => void
  onNewChat?: () => void
}

function CloseButton() {
  const { toggleSidebar } = useSidebar()
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleSidebar}
      className="h-7 w-7"
    >
      <X className="h-7 w-7 text-muted-lighter" />
      <span className="sr-only">Close Sidebar</span>
    </Button>
  )
}

function NewChatButton({ onClick }: { onClick?: () => void }) {
  const { toggleSidebar } = useSidebar()
  
  const handleClick = () => {
    toggleSidebar()
    onClick?.()
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleClick}
      className="h-7 w-7"
    >
      <PenSquare className="h-6 w-6 text-muted-lighter" />
      <span className="sr-only">New Chat</span>
    </Button>
  )
}

export function MobileSidebar({ 
  projects, 
  selectedProjectId,
  onSelectProject,
  onNewChat 
}: MobileSidebarProps) {
  const [open, setOpen] = React.useState(false)

  return (
    <SidebarProvider open={open} onOpenChange={setOpen}>
      <Sidebar className="md:hidden fixed inset-y-0 left-0 z-50" collapsible="offcanvas">
        <SidebarHeader className="flex flex-row items-center justify-between h-14 px-4 border-b">
          <CloseButton />
          <NewChatButton onClick={onNewChat} />
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenu>
                {projects.map((project) => (
                  <SidebarMenuItem key={project.id}>
                    <SidebarMenuButton
                      isActive={selectedProjectId === project.id}
                      onClick={() => {
                        onSelectProject(project.id);
                        setOpen(false);
                      }}
                    >
                      <div className="flex flex-col items-start">
                        <span className="font-medium">{project.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {project.domain.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                        </span>
                      </div>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>
      
      {/* Trigger button */}
      <div className="fixed top-4 left-4 z-50 md:hidden">
        <SidebarTrigger />
      </div>
    </SidebarProvider>
  )
} 