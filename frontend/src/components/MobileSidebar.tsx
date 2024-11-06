'use client'

import * as React from "react"
import { X, PenSquare, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Sidebar,
  SidebarHeader,
  SidebarTrigger,
  SidebarProvider,
  useSidebar
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useSession } from "next-auth/react"
import ApiClient from "@/lib/apiClient"
import { VisuallyHidden } from '@radix-ui/react-visually-hidden'
import { SettingsDialog } from '@/components/SettingsDialog'
import { LogoutButton } from "@/components/LogoutButton"
import { ChatSession, groupChatsByDate } from "@/lib/chatUtils"

interface MobileSidebarProps {
  selectedChatId: string | null
  onSelectChat: (chatId: string) => void
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

function SidebarContent({ 
  chatSessions, 
  selectedChatId, 
  onSelectChat, 
  isLoading, 
  groupedChats,
  session
}: {
  chatSessions: ChatSession[];
  selectedChatId: string | null;
  onSelectChat: (chatId: string) => void;
  isLoading: boolean;
  groupedChats: Record<string, ChatSession[]>;
  session: any;
}) {
  const { toggleSidebar } = useSidebar()
  const [isSettingsOpen, setIsSettingsOpen] = React.useState(false)
  const userName = session?.user?.full_name || session?.user?.name || "User"
  const userImage = session?.user?.image || "/path/to/default/avatar.png"

  const handleChatSelect = (chatId: string) => {
    onSelectChat(chatId);
    toggleSidebar();
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      <ScrollArea className="flex-grow px-4">
        {isLoading ? (
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8" />
          </div>
        ) : (
          <>
            {Object.entries(groupedChats).map(([dateGroup, chats]) => (
              <div key={dateGroup} className="mb-6">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">
                  {dateGroup}
                </h3>
                <div className="space-y-2">
                  {chats.map((chat) => (
                    <div
                      key={chat.id}
                      onClick={() => handleChatSelect(chat.id)}
                      className={cn(
                        "rounded-lg p-2 cursor-pointer transition-all hover:bg-muted/50",
                        selectedChatId === chat.id && "bg-muted"
                      )}
                    >
                      <div className="flex items-center justify-between space-x-2">
                        <div className="flex-grow min-w-0">
                          <div className="font-medium truncate text-sm">
                            {chat.preview.slice(0, 25)}...
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {chat.message_count} messages
                          </div>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(chat.created_at).toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {chatSessions.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                No chat history found
              </div>
            )}
          </>
        )}
      </ScrollArea>

      <div className="p-4">
        <div className="flex items-center justify-between">
          <div 
            className="flex items-center space-x-3 cursor-pointer"
            onClick={() => setIsSettingsOpen(true)}
          >
            <Avatar className="h-9 w-9 bg-primary text-foreground ring-2 ring-offset-2 ring-offset-background ring-primary">
              <AvatarImage src={userImage} alt={userName} />
              <AvatarFallback>{userName.charAt(0)}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{userName}</p>
              <p className="text-xs text-muted-foreground truncate">
                {session?.user?.email}
              </p>
            </div>
          </div>

          <LogoutButton>
            {({ logout, isLoading }) => (
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                disabled={isLoading}
                className="h-6 w-6"
                aria-label="Log out"
              >
                <LogOut className="h-5 w-5 text-muted-foreground" />
                <span className="sr-only">Log out</span>
              </Button>
            )}
          </LogoutButton>
        </div>
      </div>

      <SettingsDialog 
        open={isSettingsOpen} 
        onOpenChange={setIsSettingsOpen}
      />
    </div>
  )
}

export function MobileSidebar({ 
  selectedChatId,
  onSelectChat,
  onNewChat 
}: MobileSidebarProps) {
  const [open, setOpen] = React.useState(false)
  const [chatSessions, setChatSessions] = React.useState<ChatSession[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const { data: session } = useSession()
  
  const apiclient = React.useMemo(() => ApiClient(), [])

  React.useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const response = await apiclient.post('/chat/history', {})
        setChatSessions(response.data.chat_sessions)
      } catch (error) {
        console.error('Error fetching chat history:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchChatHistory()
  }, [apiclient])

  const groupedChats = groupChatsByDate(chatSessions)

  return (
    <SidebarProvider open={open} onOpenChange={setOpen}>
      <Sidebar 
        className="md:hidden fixed inset-y-0 left-0 z-50" 
        collapsible="offcanvas"
        aria-label="Chat history sidebar"
        title={
          <VisuallyHidden asChild>
            <h2>Chat History</h2>
          </VisuallyHidden>
        }
        description={
          <VisuallyHidden asChild>
            <p>View and manage your chat history</p>
          </VisuallyHidden>
        }
      >
        <SidebarHeader className="flex flex-row items-center justify-between h-14 px-4">
          <CloseButton />
          <NewChatButton onClick={onNewChat} />
        </SidebarHeader>
        
        <SidebarContent 
          chatSessions={chatSessions}
          selectedChatId={selectedChatId}
          onSelectChat={onSelectChat}
          isLoading={isLoading}
          groupedChats={groupedChats}
          session={session}
        />
      </Sidebar>
      
      <div className="fixed top-4 left-4 z-50 md:hidden">
        <SidebarTrigger aria-label="Open chat history" />
      </div>
    </SidebarProvider>
  )
} 