
"use client";

import * as React from "react";
import {
  BadgeCheck,
  Bell,
  ChevronsUpDown,
  ExternalLink,
  Filter,
  Link2,
  LogOut,
  MessageSquare,
  Pin,
  PlusCircle,
  Settings2,
} from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "~/components/ui/avatar";
import { Button } from "~/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "~/components/ui/tooltip";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarTrigger,
  SidebarProvider,
  useSidebar,
} from "~/components/ui/sidebar";

const data = {
  user: {
    name: "John Doe",
    email: "john@example.com",
    avatar: "/avatars/user.jpg",
  },
  recentLinks: [
    {
      title: "SNB-123: Fix authentication bug",
      url: "https://jira.atlassian.com/browse/SNB-123",
      timestamp: new Date(Date.now() - 3600000),
    },
    {
      title: "SNF-456: Implement new sidebar",
      url: "https://jira.atlassian.com/browse/SNF-456",
      timestamp: new Date(Date.now() - 86400000),
    },
    {
      title: "DEV-789: Update CI/CD pipeline",
      url: "https://dev.azure.com/browse/DEV-789",
      timestamp: new Date(Date.now() - 172800000),
    },
  ],
  chatHistory: [
    {
      id: 1,
      title: "Authentication issues",
      timestamp: new Date(Date.now() - 3600000),
      isPinned: true,
    },
    {
      id: 2,
      title: "New feature request",
      timestamp: new Date(Date.now() - 86400000),
      isPinned: true,
    },
    {
      id: 3,
      title: "Bug report for login page",
      timestamp: new Date(Date.now() - 172800000),
      isPinned: false,
    },
    {
      id: 4,
      title: "API integration questions",
      timestamp: new Date(Date.now() - 259200000),
      isPinned: false,
    },
    {
      id: 5,
      title: "Performance optimization",
      timestamp: new Date(Date.now() - 345600000),
      isPinned: false,
    },
  ],
};

function formatDate(date: Date) {
  const now = new Date();
  const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffInDays === 0) {
    return "Today";
  } else if (diffInDays === 1) {
    return "Yesterday";
  } else if (diffInDays < 7) {
    return `${diffInDays} days ago`;
  } else {
    return date.toLocaleDateString();
  }
}

function ChatSidebar() {
  const [activeFilter, setActiveFilter] = React.useState<string | null>(null);

  const filteredChats = React.useMemo(() => {
    let filtered = data.chatHistory;
    
    if (activeFilter === "pinned") {
      filtered = filtered.filter(chat => chat.isPinned);
    }
    
    return filtered;
  }, [activeFilter]);

  return (
      <TooltipProvider>
        <>
          <Sidebar collapsible="offcanvas">
            <SidebarHeader className="p-2">
              <div className="flex items-center justify-between">
                <div className="flex space-x-1">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant={activeFilter === null ? "secondary" : "ghost"} 
                        size="icon"
                        className="h-8 w-8 rounded-full"
                        onClick={() => setActiveFilter(null)}
                      >
                        <MessageSquare className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>All chats</TooltipContent>
                  </Tooltip>
                  
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant={activeFilter === "pinned" ? "secondary" : "ghost"} 
                        size="icon"
                        className="h-8 w-8 rounded-full"
                        onClick={() => setActiveFilter("pinned")}
                      >
                        <Pin className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Pinned chats</TooltipContent>
                  </Tooltip>
                  
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon"
                        className="h-8 w-8 rounded-full"
                      >
                        <Filter className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Filter chats</TooltipContent>
                  </Tooltip>
                </div>
                
                <div className="flex items-center">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8 rounded-full"
                        onClick={() => {
                          // Handle new chat
                          window.location.href = "/chat/new";
                        }}
                      >
                        <PlusCircle className="h-5 w-5" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>New chat</TooltipContent>
                  </Tooltip>
                </div>
              </div>
            </SidebarHeader>
            
            <SidebarContent>
              <SidebarGroup className="flex-1 overflow-hidden">
                <SidebarGroupLabel className="px-3 text-xs md:text-sm font-medium">Chat History</SidebarGroupLabel>
                <div className="overflow-y-auto max-h-[calc(100vh-300px)]">
                  <SidebarMenu className="flex w-full min-w-0 flex-col gap-2">
                    {filteredChats.length > 0 ? (
                      filteredChats.map((chat) => (
                        <SidebarMenuItem key={chat.id}>
                          <SidebarMenuButton asChild>
                            <a href={`/chat/${chat.id}`} className="group h-11">
                              <MessageSquare className="h-4 w-4" />
                              <div className="flex-1 overflow-hidden flex flex-col">
                                <span className="truncate text-sm md:text-base">{chat.title}</span>
                                <p className="text-xs text-muted-foreground">
                                  {formatDate(chat.timestamp)}
                                </p>
                              </div>
                              {chat.isPinned && <Pin className="h-3 w-3 text-muted-foreground" />}
                            </a>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      ))
                    ) : (
                      <div className="px-3 py-2 text-sm md:text-base text-muted-foreground">
                        No chats found
                      </div>
                    )}
                  </SidebarMenu>
                </div>
              </SidebarGroup>
              
              <SidebarGroup>
                <SidebarGroupLabel className="px-3 text-xs md:text-sm font-medium">Recent Links</SidebarGroupLabel>
                <SidebarMenu>
                  {data.recentLinks.slice(0, 3).map((link, index) => (
                    <SidebarMenuItem key={index}>
                      <SidebarMenuButton asChild>
                        <a href={link.url} target="_blank" rel="noopener noreferrer" className="group py-1.5">
                          <Link2 className="h-4 w-4" />
                          <div className="flex-1 overflow-hidden">
                            <span className="truncate">{link.title}</span>
                          </div>
                          <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                        </a>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroup>
            </SidebarContent>
            
            <SidebarFooter>
              <SidebarMenu>
                <SidebarMenuItem>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <SidebarMenuButton
                        size="sm"
                        className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                      >
                        <Avatar className="h-6 w-6 rounded-full">
                          <AvatarImage
                            src={data.user.avatar}
                            alt={data.user.name}
                          />
                          <AvatarFallback className="rounded-full">JD</AvatarFallback>
                        </Avatar>
                        <div className="grid flex-1 text-left text-sm leading-tight">
                          <span className="truncate font-medium text-xs md:text-sm">
                            {data.user.name}
                          </span>
                        </div>
                        <ChevronsUpDown className="ml-auto size-3" />
                      </SidebarMenuButton>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                      className="w-[--radix-dropdown-menu-trigger-width] min-w-48 rounded-lg"
                      side="top"
                      align="end"
                      sideOffset={4}
                    >
                      <DropdownMenuLabel className="p-0 font-normal">
                        <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                          <Avatar className="h-8 w-8 rounded-full">
                            <AvatarImage
                              src={data.user.avatar}
                              alt={data.user.name}
                            />
                            <AvatarFallback className="rounded-full">
                              JD
                            </AvatarFallback>
                          </Avatar>
                          <div className="grid flex-1 text-left text-sm leading-tight">
                            <span className="truncate font-semibold">
                              {data.user.name}
                            </span>
                            <span className="truncate text-xs">
                              {data.user.email}
                            </span>
                          </div>
                        </div>
                      </DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuGroup>
                        <DropdownMenuItem>
                          <Settings2 className="mr-2 h-4 w-4" />
                          Settings
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Bell className="mr-2 h-4 w-4" />
                          Notifications
                        </DropdownMenuItem>
                      </DropdownMenuGroup>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem>
                        <LogOut className="mr-2 h-4 w-4" />
                        Log out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarFooter>
            <SidebarRail />
          </Sidebar>
        </>
      </TooltipProvider>
  );
}


export default ChatSidebar;
